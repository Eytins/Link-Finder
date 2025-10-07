"""Core scanning functionality for Articulate Course URL Scanner."""

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


class ArticulateScanner:
    """Scanner for extracting and verifying URLs from Articulate Rise courses."""
    
    def __init__(self, headless=True):
        """Initialize the scanner with Selenium webdriver."""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        self.driver = webdriver.Chrome(options=options)
        self.visited_pages = set()
        self.all_results = []
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup driver."""
        self.driver.quit()
    
    def get_lesson_title(self, soup):
        """Extract lesson title from page."""
        title_element = soup.find('h1', class_='lesson-header__title')
        if title_element:
            return title_element.get_text(strip=True)
        return "Unknown Lesson"
    
    def get_lesson_links(self, soup, base_url):
        """Extract all lesson links from navigation sidebar."""
        lesson_links = []
        nav_links = soup.find_all('a', {'data-link': 'lesson-link-item'})
        
        for nav_link in nav_links:
            href = nav_link.get('href', '')
            if href and href.startswith('#/lessons/'):
                lesson_id = href.replace('#/lessons/', '')
                full_url = f"{base_url}#/lessons/{lesson_id}"
                
                text = nav_link.get_text(strip=True)
                lesson_title = text.split('\n')[0].strip() if '\n' in text else text
                
                lesson_links.append({
                    'url': full_url,
                    'title': lesson_title,
                    'lesson_id': lesson_id
                })
        
        return lesson_links
    
    def extract_urls_from_page(self, soup, lesson_title):
        """Extract all HTTP URLs from a page."""
        urls_found = []
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            
            if not href.startswith('http'):
                continue
            
            link_text = link_tag.get_text(strip=True)
            result_text = f"{href} is in '{lesson_title}'"
            
            urls_found.append({
                'url': href,
                'link_text': link_text,
                'lesson': lesson_title,
                'display': result_text
            })
        
        return urls_found
    
    @staticmethod
    def verify_url(url, timeout=10):
        """Verify if a URL is accessible and return status information."""
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
    
    @staticmethod
    def is_similar_page(url):
        """Check if URL is a similar Rise/Articulate course page."""
        parsed = urlparse(url)
        if 'rise.articulate.com' in parsed.netloc and '/share/' in parsed.path:
            return True
        return False
    
    @staticmethod
    def get_base_url(url):
        """Extract base URL from a full URL."""
        if '#' in url:
            return url.split('#')[0]
        return url
    
    def scan_course(self, course_url, depth=0, max_depth=2, verbose=True):
        """Recursively scan a course and all linked courses."""
        base_url = self.get_base_url(course_url)
        
        if base_url in self.visited_pages:
            return
        
        self.visited_pages.add(base_url)
        indent = "  " * depth
        
        if verbose:
            print(f"{indent}Scanning course: {base_url}")
        
        try:
            self.driver.get(course_url)
            time.sleep(5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            lesson_links = self.get_lesson_links(soup, base_url)
            
            if verbose:
                print(f"{indent}Found {len(lesson_links)} lessons")
            
            external_courses = set()
            
            for i, lesson in enumerate(lesson_links, 1):
                if verbose:
                    print(f"{indent}  [{i}/{len(lesson_links)}] {lesson['title']}")
                
                self.driver.get(lesson['url'])
                time.sleep(3)
                
                lesson_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                lesson_title = self.get_lesson_title(lesson_soup)
                
                urls = self.extract_urls_from_page(lesson_soup, lesson_title)
                
                for url_data in urls:
                    if not any(r['display'] == url_data['display'] for r in self.all_results):
                        self.all_results.append(url_data)
                    
                    if self.is_similar_page(url_data['url']) and depth < max_depth:
                        external_courses.add(url_data['url'])
            
            if external_courses and depth < max_depth:
                if verbose:
                    print(f"\n{indent}Found {len(external_courses)} linked courses to scan...")
                for ext_course in external_courses:
                    self.scan_course(ext_course, depth + 1, max_depth, verbose)
        
        except Exception as e:
            if verbose:
                print(f"{indent}Error scanning {course_url}: {e}")
    
    def verify_all_urls(self, max_workers=10, verbose=True):
        """Verify all discovered URLs in parallel."""
        unique_urls = {}
        for result in self.all_results:
            if result['url'] not in unique_urls:
                unique_urls[result['url']] = []
            unique_urls[result['url']].append(result)
        
        if verbose:
            print(f"Verifying {len(unique_urls)} unique URLs...\n")
        
        verified_results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.verify_url, url): url for url in unique_urls.keys()}
            
            for i, future in enumerate(as_completed(future_to_url), 1):
                url = future_to_url[future]
                if verbose:
                    print(f"[{i}/{len(unique_urls)}] Checking {url[:80]}...")
                try:
                    verification = future.result()
                    verified_results[url] = verification
                except Exception as e:
                    verified_results[url] = {'status': 'ERROR', 'code': None, 'message': str(e)}
        
        return verified_results, unique_urls
