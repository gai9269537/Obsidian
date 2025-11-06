#!/usr/bin/env python3
"""
Query DataHub GraphQL API to fetch one or more dataset domain associations and print them.

Usage:
  python3 scripts/check_domain.py [--gms GMS_URL] [--retries N] [--delay S] [--timeout S] [--json] <urn1> [<urn2> ...]

Examples:
  python3 scripts/check_domain.py "urn:li:dataset:(urn:li:dataPlatform:obsidian,obsidian.Kha.Python,PROD)"
  python3 scripts/check_domain.py --json urn1 urn2

Features:
  - Accepts multiple URNs
  - Retries network requests with backoff
  - Machine-friendly JSON output (aggregated)
"""
import argparse
import json
import time
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin


DEFAULT_GMS = "http://localhost:8080"


def graphql_query(gms_url: str, query: str, variables: dict, timeout: float = 10.0):
    url = urljoin(gms_url, '/api/graphql')
    payload = json.dumps({"query": query, "variables": variables}).encode('utf-8')
    req = Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    with urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_domain_for_urn(urn: str, gms: str, timeout: float):
    query = '''query dataset($urn: String!) {
      dataset(urn: $urn) {
        urn
        domain {
          associatedUrn
          domain {
            urn
            id
            properties { name description }
          }
        }
      }
    }'''
    variables = {"urn": urn}
    resp = graphql_query(gms, query, variables, timeout=timeout)
    # Handle GraphQL errors
    if resp is None:
        return {'urn': urn, 'error': 'no_response', 'domain': None}
    if 'errors' in resp and resp['errors']:
        return {'urn': urn, 'error': 'graphql_errors', 'errors': resp['errors'], 'domain': None}
    data = resp.get('data', {}) or {}
    dataset = data.get('dataset')
    if not dataset:
        return {'urn': urn, 'error': 'not_found', 'domain': None}
    domain_assoc = dataset.get('domain')
    if not domain_assoc:
        return {'urn': urn, 'error': None, 'domain': None}
    dom = domain_assoc.get('domain')
    return {'urn': urn, 'error': None, 'domain': dom}


def fetch_with_retries(urn: str, gms: str, retries: int, delay: float, timeout: float):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fetch_domain_for_urn(urn, gms, timeout=timeout)
        except (HTTPError, URLError) as e:
            last_exc = e
            if attempt < retries:
                time.sleep(delay)
                continue
            return {'urn': urn, 'error': 'network_error', 'exception': str(e), 'domain': None}
        except Exception as e:
            last_exc = e
            return {'urn': urn, 'error': 'exception', 'exception': str(e), 'domain': None}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check DataHub dataset domains via GraphQL')
    parser.add_argument('--gms', default=DEFAULT_GMS, help='DataHub GMS base URL')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries for network calls')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay (seconds) between retries')
    parser.add_argument('--timeout', type=float, default=10.0, help='Request timeout (seconds)')
    parser.add_argument('--json', action='store_true', help='Output aggregated JSON array')
    parser.add_argument('urns', nargs='+', help='One or more dataset URNs to check')
    args = parser.parse_args(argv)

    results = []
    for urn in args.urns:
        r = fetch_with_retries(urn, args.gms, retries=args.retries, delay=args.delay, timeout=args.timeout)
        results.append(r)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Human readable
        for r in results:
            urn = r.get('urn')
            if r.get('error'):
                print(f"{urn}: ERROR={r.get('error')} {r.get('exception','')}")
                if r.get('errors'):
                    print(json.dumps(r.get('errors'), indent=2))
            else:
                dom = r.get('domain')
                if not dom:
                    print(f"{urn}: no domain assigned")
                else:
                    print(f"{urn}: domain={dom.get('id')} ({dom.get('urn')})")
                    props = dom.get('properties') or {}
                    if props:
                        print(f"  name: {props.get('name')}")
                        if props.get('description'):
                            print(f"  desc: {props.get('description')}")

    # Return non-zero if any network errors occurred
    for r in results:
        if r.get('error') in ('network_error','exception'):
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
