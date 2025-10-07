from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Step 1: Set up Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in background
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=options)

# Keep track of visited pages to avoid infinite loops
visited_pages = set()
all_results = []

def get_lesson_title(soup):
    """Extract lesson title from page"""
    title_element = soup.find('h1', class_='lesson-header__title')
    if title_element:
        return title_element.get_text(strip=True)
    return "Unknown Lesson"

def get_lesson_links(soup, base_url):
    """Extract all lesson links from navigation sidebar"""
    lesson_links = []
    nav_links = soup.find_all('a', {'data-link': 'lesson-link-item'})
    
    for nav_link in nav_links:
        href = nav_link.get('href', '')
        if href and href.startswith('#/lessons/'):
            lesson_id = href.replace('#/lessons/', '')
            full_url = f"{base_url}#/lessons/{lesson_id}"
            
            # Get lesson title from navigation
            text = nav_link.get_text(strip=True)
            # Remove progress indicators and extra text
            lesson_title = text.split('\n')[0].strip() if '\n' in text else text
            
            lesson_links.append({
                'url': full_url,
                'title': lesson_title,
                'lesson_id': lesson_id
            })
    
    return lesson_links

def extract_urls_from_page(soup, lesson_title):
    """Extract all HTTP URLs from a page"""
    urls_found = []
    
    for link_tag in soup.find_all('a', href=True):
        href = link_tag['href']
        
        # Skip non-http links
        if not href.startswith('http'):
            continue
        
        # Get the link text
        link_text = link_tag.get_text(strip=True)
        
        # Create result in the desired format
        result_text = f"{href} is in '{lesson_title}'"
        
        urls_found.append({
            'url': href,
            'link_text': link_text,
            'lesson': lesson_title,
            'display': result_text
        })
    
    return urls_found

def verify_url(url, timeout=10):
    """Verify if a URL is accessible and return status information"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        status_code = response.status_code
        
        if status_code == 200:
            return {
                'status': 'OK',
                'code': status_code,
                'message': 'URL is accessible'
            }
        elif 300 <= status_code < 400:
            return {
                'status': 'WARNING',
                'code': status_code,
                'message': f'Redirects to {response.url}'
            }
        elif 400 <= status_code < 500:
            return {
                'status': 'BROKEN',
                'code': status_code,
                'message': 'Client error (page not found or forbidden)'
            }
        elif 500 <= status_code < 600:
            return {
                'status': 'BROKEN',
                'code': status_code,
                'message': 'Server error'
            }
        else:
            return {
                'status': 'WARNING',
                'code': status_code,
                'message': f'Unexpected status code: {status_code}'
            }
    except requests.exceptions.Timeout:
        return {
            'status': 'ERROR',
            'code': None,
            'message': 'Request timed out'
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'BROKEN',
            'code': None,
            'message': 'Connection failed'
        }
    except requests.exceptions.TooManyRedirects:
        return {
            'status': 'WARNING',
            'code': None,
            'message': 'Too many redirects'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'code': None,
            'message': f'Error: {str(e)}'
        }

def is_similar_page(url):
    """Check if URL is a similar Rise/Articulate course page"""
    parsed = urlparse(url)
    # Check if it's a Rise course URL
    if 'rise.articulate.com' in parsed.netloc and '/share/' in parsed.path:
        return True
    return False

def get_base_url(url):
    """Extract base URL from a full URL"""
    if '#' in url:
        return url.split('#')[0]
    return url

def scan_course(course_url, depth=0, max_depth=2):
    """Recursively scan a course and all linked courses"""
    global visited_pages, all_results
    
    base_url = get_base_url(course_url)
    
    # Check if already visited
    if base_url in visited_pages:
        return
    
    visited_pages.add(base_url)
    indent = "  " * depth
    
    print(f"{indent}Scanning course: {base_url}")
    
    try:
        # Load the main page
        driver.get(course_url)
        time.sleep(5)
        
        # Parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Get all lesson links
        lesson_links = get_lesson_links(soup, base_url)
        print(f"{indent}Found {len(lesson_links)} lessons")
        
        # Track external course links found
        external_courses = set()
        
        # Visit each lesson
        for i, lesson in enumerate(lesson_links, 1):
            print(f"{indent}  [{i}/{len(lesson_links)}] {lesson['title']}")
            
            # Navigate to lesson
            driver.get(lesson['url'])
            time.sleep(3)
            
            # Parse lesson page
            lesson_soup = BeautifulSoup(driver.page_source, 'html.parser')
            lesson_title = get_lesson_title(lesson_soup)
            
            # Extract URLs from this lesson
            urls = extract_urls_from_page(lesson_soup, lesson_title)
            
            # Add to results (avoid duplicates)
            for url_data in urls:
                if not any(r['display'] == url_data['display'] for r in all_results):
                    all_results.append(url_data)
                
                # Check if this is a link to another similar course
                if is_similar_page(url_data['url']) and depth < max_depth:
                    external_courses.add(url_data['url'])
        
        # Recursively scan linked courses
        if external_courses and depth < max_depth:
            print(f"\n{indent}Found {len(external_courses)} linked courses to scan...")
            for ext_course in external_courses:
                scan_course(ext_course, depth + 1, max_depth)
    
    except Exception as e:
        print(f"{indent}Error scanning {course_url}: {e}")

try:
    # Step 2: Get URL from user input
    print("="*80)
    print("Articulate Course URL Scanner")
    print("="*80)
    
    # Check if URL was provided as command line argument
    if len(sys.argv) > 1:
        main_url = sys.argv[1]
        print(f"Using URL from command line: {main_url}")
    else:
        # Prompt user for URL
        main_url = input("\nPlease enter the Articulate Rise course URL: ").strip()
    
    # Validate URL
    if not main_url:
        print("Error: No URL provided. Exiting.")
        sys.exit(1)
    
    if not main_url.startswith('http'):
        print("Error: Invalid URL format. URL must start with http:// or https://")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("Starting recursive URL extraction...")
    print("="*80 + "\n")
    
    scan_course(main_url)
    
    print(f"\n{'='*80}")
    print(f"URL EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Total unique URLs found: {len(all_results)}")
    print(f"Total pages visited: {len(visited_pages)}")
    print(f"\n{'='*80}")
    print("VERIFYING URLs...")
    print(f"{'='*80}\n")
    
    # Step 3: Verify all URLs
    # Get unique URLs to verify
    unique_urls = {}
    for result in all_results:
        if result['url'] not in unique_urls:
            unique_urls[result['url']] = []
        unique_urls[result['url']].append(result)
    
    print(f"Verifying {len(unique_urls)} unique URLs...\n")
    
    # Verify URLs in parallel for speed
    verified_results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(verify_url, url): url for url in unique_urls.keys()}
        
        for i, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            print(f"[{i}/{len(unique_urls)}] Checking {url[:80]}...")
            try:
                verification = future.result()
                verified_results[url] = verification
            except Exception as e:
                verified_results[url] = {'status': 'ERROR', 'code': None, 'message': str(e)}
    
    # Step 4: Display results with verification status
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS WITH VERIFICATION")
    print(f"{'='*80}\n")
    
    working_count = 0
    warning_count = 0
    broken_count = 0
    error_count = 0
    
    for i, result in enumerate(all_results, 1):
        url = result['url']
        verification = verified_results.get(url, {'status': 'UNKNOWN', 'message': 'Not verified'})
        
        status = verification['status']
        if status == 'OK':
            status_icon = '✓'
            working_count += 1
        elif status == 'WARNING':
            status_icon = '⚠'
            warning_count += 1
        elif status == 'BROKEN':
            status_icon = '✗'
            broken_count += 1
        else:
            status_icon = '?'
            error_count += 1
        
        print(f"{i}. [{status_icon} {status}] {result['display']}")
        if result['link_text']:
            print(f"   Link text: {result['link_text']}")
        print(f"   Verification: {verification['message']}")
        if verification['code']:
            print(f"   HTTP Status: {verification['code']}")
        print()
    
    # Step 5: Summary
    print(f"{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total URLs: {len(all_results)}")
    print(f"Unique URLs: {len(unique_urls)}")
    print(f"✓ Working: {working_count}")
    print(f"⚠ Warnings: {warning_count}")
    print(f"✗ Broken: {broken_count}")
    print(f"? Errors: {error_count}")
    print(f"{'='*80}")

finally:
    driver.quit()
