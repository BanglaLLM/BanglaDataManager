import asyncio
import csv
import json
import re
import urllib.parse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
import aiofiles
import logging
from datetime import datetime

# Fix imports - use the corrected paths based on your structure
from browser_controller import BrowserController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsEvent:
    """Domain model for a news event from CSV"""
    year: str
    ruling_party: str
    event: str
    news_headline: str = ""
    news_body: str = ""
    
    def get_search_query(self) -> str:
        """Generate main search query"""
        return f"{self.event}"
    
    def get_exact_phrase(self) -> str:
        """Generate exact phrase for advanced search"""
        return self.event
    
    def get_file_safe_name(self) -> str:
        """Generate file-safe name for this event"""
        safe_name = re.sub(r'[^\w\s-]', '', self.event)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        return f"{self.year}_{safe_name[:50]}"

@dataclass
class SearchResult:
    """Represents a single search result from Google"""
    title: str
    url: str
    snippet: str
    source_domain: str

class SimpleGoogleScraper:
    """Simplified Google scraper that follows your exact workflow with advanced search"""
    
    def __init__(self, browser: BrowserController):
        self.browser = browser
        self.visited_urls: Set[str] = set()
        
    async def search_event(self, event: NewsEvent, max_pages: int = 50) -> List[SearchResult]:
        """
        Step 1: Go directly to Google Advanced Search URL
        Step 2: Navigate through all pages and extract URLs
        """
        logger.info(f"🔍 Advanced searching for: {event.get_search_query()}")
        
        try:
            # Step 1: Build and navigate to advanced search URL
            search_url = self._build_advanced_search_url(event)
            logger.info(f"🌐 Navigating to: {search_url}")
            
            await self.browser.goto(search_url, timeout=30000)
            await asyncio.sleep(3)  # Wait for results to load
            
            all_results = []
            page_count = 0
            
            # Step 2: Navigate through pages and extract URLs
            while page_count < max_pages:
                page_count += 1
                logger.info(f"📄 Processing search results page {page_count}/{max_pages}")
                
                # Scroll to bottom to ensure all results are loaded
                await self._scroll_to_bottom()
                
                # Extract search results from current page
                page_results = await self._extract_search_results_from_page()
                all_results.extend(page_results)
                
                logger.info(f"📋 Found {len(page_results)} results on page {page_count} (Total: {len(all_results)})")
                
                # Try to go to next page
                if page_count < max_pages:
                    logger.info(f"🔄 Attempting to navigate to page {page_count + 1}")
                    next_success = await self._go_to_next_search_page()
                    if not next_success:
                        logger.info(f"📝 No more pages available after page {page_count}")
                        break
                    await asyncio.sleep(4)  # Increased wait time for next page to load
                else:
                    logger.info(f"📝 Reached maximum pages limit ({max_pages})")
                    break
            
            logger.info(f"✅ Total URLs collected: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Error during search: {e}")
            return []
    
    def _build_advanced_search_url(self, event: NewsEvent) -> str:
        """Build Google advanced search URL with Bangladesh focus like your examples"""
        params = {
            'as_q': event.get_search_query(),           # Main query with year and Bangladesh
            # 'as_epq': event.get_exact_phrase(),         # Exact phrase from event
            'as_oq': '',                                # Any of these words
            'as_eq': '',                                # None of these words
            'as_nlo': '',                               # Numbers from
            'as_nhi': '',                               # Numbers to
            'lr': '',                                   # Language
            'cr': 'countryBD',                          # Country: Bangladesh
            'as_qdr': 'all',                            # Date range: all time
            'as_sitesearch': '',                        # Site search
            'as_occt': 'any',                           # Where terms occur
            'as_filetype': '',                          # File type
            'tbs': '',                                  # Additional filters
        }
        
        # Remove empty parameters to clean up URL
        filtered_params = {k: v for k, v in params.items() if v}
        
        base_url = "https://www.google.com/search"
        url = f"{base_url}?" + urllib.parse.urlencode(filtered_params, quote_via=urllib.parse.quote)
        logger.info(f"🔍 Advanced search URL: {url}")
        return url
    
    async def _scroll_to_bottom(self):
        """Scroll to bottom of page to load all results"""
        try:
            # Scroll down multiple times to ensure all content is loaded
            for i in range(3):
                await self.browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                
            # Scroll back to see pagination
            await self.browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight - 500)")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error scrolling: {e}")
    
    async def _extract_search_results_from_page(self) -> List[SearchResult]:
        """Extract all search result URLs from current page"""
        try:
            extract_js = """
            () => {
                const results = [];
                
                // Multiple selectors to catch different Google layouts
                const linkSelectors = [
                    'div[data-ved] h3 a',
                    'div.g h3 a', 
                    'div[jscontroller] h3 a',
                    'div.yuRUbf a',
                    'a[jsname="UWckNb"]'
                ];
                
                const allLinks = [];
                linkSelectors.forEach(selector => {
                    const links = document.querySelectorAll(selector);
                    allLinks.push(...links);
                });
                
                allLinks.forEach((link, index) => {
                    try {
                        const url = link.href;
                        const title = link.textContent || link.innerText || '';
                        
                        // Find snippet/description
                        let snippet = '';
                        const resultContainer = link.closest('div.g, div[data-ved], div[jscontroller], div.yuRUbf');
                        if (resultContainer) {
                            const snippetElements = resultContainer.querySelectorAll('span, div');
                            for (let el of snippetElements) {
                                if (el.textContent && el.textContent.length > 50 && !el.querySelector('a')) {
                                    snippet = el.textContent.substring(0, 200);
                                    break;
                                }
                            }
                        }
                        
                        // Extract domain
                        let domain = 'unknown';
                        try {
                            domain = new URL(url).hostname;
                        } catch (e) {
                            domain = 'unknown';
                        }
                        
                        // Filter valid URLs
                        if (url && 
                            url.startsWith('http') &&
                            !url.includes('google.com/search') && 
                            !url.includes('webcache.googleusercontent.com') &&
                            !url.includes('translate.google.com') &&
                            !url.includes('maps.google.com') &&
                            title.length > 0) {
                            
                            results.push({
                                title: title.trim(),
                                url: url,
                                snippet: snippet.trim(),
                                domain: domain
                            });
                        }
                    } catch (e) {
                        console.log('Error processing link:', e);
                    }
                });
                
                // Remove duplicates
                const unique = [];
                const seen = new Set();
                results.forEach(result => {
                    if (!seen.has(result.url)) {
                        seen.add(result.url);
                        unique.push(result);
                    }
                });
                
                return unique;
            }
            """
            
            raw_results = await self.browser.page.evaluate(extract_js)
            
            search_results = []
            for result_data in raw_results:
                search_results.append(SearchResult(
                    title=result_data['title'],
                    url=result_data['url'],
                    snippet=result_data['snippet'],
                    source_domain=result_data['domain']
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Error extracting search results: {e}")
            return []
    
    async def _go_to_next_search_page(self) -> bool:
        """Navigate to next page of search results - improved detection"""
        try:
            # First scroll to bottom to see pagination
            await self._scroll_to_bottom()
            
            # More comprehensive next page detection
            next_page_js = """
            () => {
                // Multiple strategies to find next page button
                
                // Strategy 1: Look for standard Next button patterns
                const nextSelectors = [
                    'a[aria-label*="Next"]',
                    'a[aria-label*="পরবর্তী"]',  // Bengali "Next"
                    'a#pnnext',
                    'a[id="pnnext"]',
                    'span[style*="cursor:pointer"][id="pnnext"]'
                ];
                
                for (let selector of nextSelectors) {
                    const nextButton = document.querySelector(selector);
                    if (nextButton && nextButton.href && !nextButton.disabled && nextButton.style.display !== 'none') {
                        console.log('Found next button with selector:', selector);
                        nextButton.click();
                        return true;
                    }
                }
                
                // Strategy 2: Look for pagination numbers and find the next one
                const currentPageNumber = document.querySelector('span[aria-label*="Page"]:not([aria-label*="Next"])');
                if (currentPageNumber) {
                    const currentNum = parseInt(currentPageNumber.textContent);
                    const nextNum = currentNum + 1;
                    
                    // Look for the next page number link
                    const pageLinks = document.querySelectorAll('a[href*="start="]');
                    for (let link of pageLinks) {
                        if (link.textContent.trim() === nextNum.toString()) {
                            console.log('Found next page number:', nextNum);
                            link.click();
                            return true;
                        }
                    }
                }
                
                // Strategy 3: Look for any pagination link that might be next
                const allPageLinks = document.querySelectorAll('a[href*="start="]');
                for (let link of allPageLinks) {
                    // Check if this link has a higher start parameter than current
                    const match = link.href.match(/start=(\d+)/);
                    if (match) {
                        const startValue = parseInt(match[1]);
                        // If this is a reasonable next page (10, 20, 30, etc.)
                        if (startValue > 0 && startValue % 10 === 0) {
                            console.log('Found pagination link with start:', startValue);
                            link.click();
                            return true;
                        }
                    }
                }
                
                // Strategy 4: Look for any clickable element that might be next
                const potentialNext = document.querySelectorAll('a, span, td');
                for (let element of potentialNext) {
                    const text = element.textContent.toLowerCase().trim();
                    if ((text === 'next' || text === 'পরবর্তী' || text === '>') && 
                        element.href && 
                        element.href.includes('start=')) {
                        console.log('Found potential next element:', text);
                        element.click();
                        return true;
                    }
                }
                
                console.log('No next page button found');
                return false;
            }
            """
            
            clicked = await self.browser.page.evaluate(next_page_js)
            
            if clicked:
                logger.info("➡️ Successfully navigated to next page")
                return True
            else:
                logger.warning("⚠️ Could not find next page button")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error going to next page: {e}")
            return False
    
    async def save_content_from_urls(self, urls: List[SearchResult], event: NewsEvent, output_dir: Path) -> List[Dict]:
        """
        Step 3: Visit each URL and save the HTML content
        """
        logger.info(f"📥 Starting to collect content from {len(urls)} URLs")
        
        # Create event directory
        event_dir = output_dir / event.get_file_safe_name()
        event_dir.mkdir(exist_ok=True)
        
        collected_content = []
        
        for i, search_result in enumerate(urls):
            if search_result.url in self.visited_urls:
                logger.info(f"⏭️ Skipping already visited: {search_result.url}")
                continue
                
            try:
                logger.info(f"🌐 Visiting {i+1}/{len(urls)}: {search_result.url}")
                
                # Navigate to the URL
                await self.browser.goto(search_result.url, timeout=20000)
                await asyncio.sleep(2)  # Let page load
                
                # Get the HTML content
                html_content = await self.browser.page.content()
                
                # Save the HTML file
                filename = f"content_{i+1:03d}_{search_result.source_domain.replace('.', '_')}.html"
                file_path = event_dir / filename
                
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(html_content)
                
                # Track what we collected
                content_info = {
                    'url': search_result.url,
                    'title': search_result.title,
                    'domain': search_result.source_domain,
                    'local_file': str(file_path),
                    'file_size': len(html_content),
                    'timestamp': datetime.now().isoformat()
                }
                
                collected_content.append(content_info)
                self.visited_urls.add(search_result.url)
                
                logger.info(f"✅ Saved: {filename} ({len(html_content)} bytes)")
                
            except Exception as e:
                logger.error(f"❌ Failed to collect from {search_result.url}: {e}")
                continue
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        logger.info(f"📊 Successfully collected {len(collected_content)} content files")
        return collected_content

class SimpleBangladeshNewsScraper:
    """Main scraper with simplified workflow and advanced search"""
    
    def __init__(self, csv_file_path: str, output_dir: str = "scraped_news", 
                 headless: bool = True, proxy: dict = None):
        self.csv_file_path = Path(csv_file_path)
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.proxy = proxy
        self.max_pages_per_event = 50  # Increased from 3 to 15 to get more results
        
    def load_events_from_csv(self) -> List[NewsEvent]:
        """Load news events from CSV file"""
        events = []
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                # Auto-detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                delimiter = ',' if ',' in sample else '\t'
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row in reader:
                    year = row.get('Year', row.get('year', '')).strip()
                    ruling_party = row.get('Ruling Party', row.get('ruling_party', '')).strip()
                    event = row.get('Event', row.get('event', '')).strip()
                    
                    if year and event:
                        events.append(NewsEvent(
                            year=year,
                            ruling_party=ruling_party,
                            event=event
                        ))
                
                logger.info(f"📊 Loaded {len(events)} events from CSV")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error loading CSV: {e}")
            return []
    
    async def scrape_all_events(self, start_index: int = 0, max_events: Optional[int] = None):
        """Main scraping workflow with advanced search"""
        events = self.load_events_from_csv()
        
        if not events:
            logger.error("❌ No events to process")
            return
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Determine which events to process
        end_index = len(events)
        if max_events:
            end_index = min(start_index + max_events, len(events))
        
        events_to_process = events[start_index:end_index]
        logger.info(f"🚀 Processing {len(events_to_process)} events")
        logger.info(f"📄 Max pages per event: {self.max_pages_per_event}")
        
        # Initialize browser
        async with BrowserController(self.headless, self.proxy, enable_streaming=False) as browser:
            scraper = SimpleGoogleScraper(browser)
            
            overall_summary = {
                'total_events_processed': 0,
                'successful_events': 0,
                'total_urls_collected': 0,
                'total_files_saved': 0,
                'start_time': datetime.now().isoformat(),
                'max_pages_per_event': self.max_pages_per_event,
                'events_results': []
            }
            
            for i, event in enumerate(events_to_process):
                logger.info(f"\n{'='*60}")
                logger.info(f"🎯 Processing {start_index + i + 1}/{len(events)}: {event.event}")
                logger.info(f"📅 Year: {event.year}")
                logger.info(f"🔍 Search query: {event.get_search_query()}")
                logger.info(f"📝 Exact phrase: {event.get_exact_phrase()}")
                logger.info(f"{'='*60}")
                
                try:
                    # Step 1 & 2: Advanced search and collect URLs
                    search_results = await scraper.search_event(event, self.max_pages_per_event)
                    
                    if not search_results:
                        logger.warning(f"⚠️ No search results found for: {event.event}")
                        continue
                    
                    # Step 3: Visit URLs and save content
                    collected_content = await scraper.save_content_from_urls(search_results, event, self.output_dir)
                    
                    # Save event summary
                    event_summary = {
                        'event': asdict(event),
                        'search_results_count': len(search_results),
                        'content_files_saved': len(collected_content),
                        'search_results': [asdict(result) for result in search_results],
                        'collected_files': collected_content
                    }
                    
                    # Save summary to file
                    event_dir = self.output_dir / event.get_file_safe_name()
                    summary_file = event_dir / "event_summary.json"
                    async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(event_summary, indent=2, ensure_ascii=False))
                    
                    overall_summary['events_results'].append(event_summary)
                    overall_summary['total_events_processed'] += 1
                    overall_summary['total_urls_collected'] += len(search_results)
                    overall_summary['total_files_saved'] += len(collected_content)
                    
                    if len(collected_content) > 0:
                        overall_summary['successful_events'] += 1
                    
                    logger.info(f"✅ Event completed: {len(collected_content)} files saved from {len(search_results)} URLs")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process {event.event}: {e}")
                
                # Pause between events
                await asyncio.sleep(3)
            
            # Save overall summary
            overall_summary['end_time'] = datetime.now().isoformat()
            summary_file = self.output_dir / "scraping_summary.json"
            async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(overall_summary, indent=2, ensure_ascii=False))
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🏁 SCRAPING COMPLETED")
            logger.info(f"📊 Events processed: {overall_summary['total_events_processed']}")
            logger.info(f"✅ Successful events: {overall_summary['successful_events']}")
            logger.info(f"🔗 Total URLs collected: {overall_summary['total_urls_collected']}")
            logger.info(f"📁 Total files saved: {overall_summary['total_files_saved']}")
            logger.info(f"📄 Max pages per event: {overall_summary['max_pages_per_event']}")
            logger.info(f"💾 Output directory: {self.output_dir}")
            logger.info(f"{'='*60}")

# Main execution
async def main():
    """Run the updated scraper with advanced search"""
    scraper = SimpleBangladeshNewsScraper(
        csv_file_path="bangladesh_news_events.csv",
        output_dir="scraped_news",
        headless=False,  # Set to True to hide browser
        proxy=None
    )
    
    # Start scraping - process just 1 event for testing
    await scraper.scrape_all_events(
        start_index=0,
        max_events=1  # Process just first event for testing
    )

if __name__ == "__main__":
    asyncio.run(main())