
"""Command-line interface for Articulate Course URL Scanner."""

import argparse
import sys
from articulate_scanner.scanner import ArticulateScanner


def print_results(scanner, verified_results, unique_urls):
    """Print formatted results."""
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS WITH VERIFICATION")
    print(f"{'='*80}\n")
    
    working_count = 0
    warning_count = 0
    broken_count = 0
    error_count = 0
    
    for i, result in enumerate(scanner.all_results, 1):
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
    
    print(f"{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total URLs: {len(scanner.all_results)}")
    print(f"Unique URLs: {len(unique_urls)}")
    print(f"✓ Working: {working_count}")
    print(f"⚠ Warnings: {warning_count}")
    print(f"✗ Broken: {broken_count}")
    print(f"? Errors: {error_count}")
    print(f"{'='*80}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Scan Articulate Rise courses for URLs and verify their status.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a course and verify all URLs
  articulate-scanner https://rise.articulate.com/share/your-course-id
  
  # Scan without verification
  articulate-scanner https://rise.articulate.com/share/your-course-id --no-verify
  
  # Limit recursion depth
  articulate-scanner https://rise.articulate.com/share/your-course-id --max-depth 1
  
  # Run in non-headless mode (show browser)
  articulate-scanner https://rise.articulate.com/share/your-course-id --no-headless
        """
    )
    
    parser.add_argument(
        'url',
        help='Articulate Rise course URL to scan'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=2,
        help='Maximum recursion depth for linked courses (default: 2)'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip URL verification step'
    )
    
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=10,
        help='Maximum parallel workers for URL verification (default: 10)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith('http'):
        print("Error: Invalid URL format. URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)
    
    verbose = not args.quiet
    
    if verbose:
        print("="*80)
        print("Articulate Course URL Scanner")
        print("="*80)
        print(f"\nScanning: {args.url}")
        print(f"Max depth: {args.max_depth}")
        print(f"Verification: {'Disabled' if args.no_verify else 'Enabled'}")
        print("\n" + "="*80)
        print("Starting recursive URL extraction...")
        print("="*80 + "\n")
    
    try:
        with ArticulateScanner(headless=not args.no_headless) as scanner:
            # Scan the course
            scanner.scan_course(args.url, max_depth=args.max_depth, verbose=verbose)
            
            if verbose:
                print(f"\n{'='*80}")
                print(f"URL EXTRACTION COMPLETE")
                print(f"{'='*80}")
                print(f"Total unique URLs found: {len(scanner.all_results)}")
                print(f"Total pages visited: {len(scanner.visited_pages)}")
            
            # Verify URLs if requested
            if not args.no_verify:
                if verbose:
                    print(f"\n{'='*80}")
                    print("VERIFYING URLs...")
                    print(f"{'='*80}\n")
                
                verified_results, unique_urls = scanner.verify_all_urls(
                    max_workers=args.max_workers,
                    verbose=verbose
                )
                
                print_results(scanner, verified_results, unique_urls)
            else:
                # Print results without verification
                if verbose:
                    print(f"\n{'='*80}")
                    print(f"RESULTS (No Verification)")
                    print(f"{'='*80}\n")
                
                for i, result in enumerate(scanner.all_results, 1):
                    print(f"{i}. {result['display']}")
                    if result['link_text']:
                        print(f"   Link text: {result['link_text']}")
                    print()
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
