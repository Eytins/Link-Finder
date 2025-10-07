from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

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
    # Step 2: Start scanning from the main course
    main_url = "https://rise.articulate.com/share/dRLwd_Wtqs4StJOHb33qJeC_d4ZivRHc"

    print("=" * 80)
    print("Starting recursive URL extraction...")
    print("=" * 80 + "\n")

    scan_course(main_url)

    # Step 3: Display all results
    print(f"\n{'=' * 80}")
    print(f"FINAL RESULTS")
    print(f"{'=' * 80}")
    print(f"Total unique URLs found: {len(all_results)}")
    print(f"Total pages visited: {len(visited_pages)}")
    print(f"{'=' * 80}\n")

    for i, result in enumerate(all_results, 1):
        print(f"{i}. {result['display']}")
        if result['link_text']:
            print(f"   Link text: {result['link_text']}")
        print()

finally:
    driver.quit()