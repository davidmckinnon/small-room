#!/usr/bin/env python3
"""Look up a film by title and add it to films.json."""

import json
import os
import sys
import urllib.request
import urllib.parse

FILMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'films.json')
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.omdb_key')

def get_api_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            return f.read().strip()
    key = os.environ.get('OMDB_API_KEY')
    if key:
        return key
    print("No OMDb API key found.")
    print("Get a free key at: https://www.omdbapi.com/apikey.aspx")
    print("Then either:")
    print(f"  - Save it to {KEY_FILE}")
    print("  - Or set OMDB_API_KEY environment variable")
    key = input("\nOr paste your key here: ").strip()
    if key:
        with open(KEY_FILE, 'w') as f:
            f.write(key)
        print(f"Key saved to {KEY_FILE}\n")
        return key
    sys.exit(1)

def search_film(title, year=None):
    key = get_api_key()
    params = {'apikey': key, 't': title, 'type': 'movie'}
    if year:
        params['y'] = year
    url = 'https://www.omdbapi.com/?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("API key not authorised.")
            print("Check your email for the OMDb activation link and click it,")
            print("then try again.")
            sys.exit(1)
        raise
    if data.get('Response') == 'False':
        print(f"Not found: {data.get('Error', 'Unknown error')}")
        # Try a search instead
        params2 = {'apikey': key, 's': title, 'type': 'movie'}
        url2 = 'https://www.omdbapi.com/?' + urllib.parse.urlencode(params2)
        with urllib.request.urlopen(url2) as resp2:
            results = json.loads(resp2.read())
        if results.get('Search'):
            print("\nDid you mean one of these?")
            for i, r in enumerate(results['Search'][:5], 1):
                print(f"  {i}. {r['Title']} ({r['Year']})")
            choice = input("\nEnter number (or 0 to cancel): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(results['Search'][:5]):
                picked = results['Search'][int(choice) - 1]
                return search_film(picked['Title'], picked['Year'])
        return None
    return data

def load_films():
    if os.path.exists(FILMS_FILE):
        with open(FILMS_FILE) as f:
            return json.load(f)
    return {"films": [], "candidates": []}

def save_films(data):
    with open(FILMS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def make_id(title):
    return title.lower().replace(' ', '_').replace("'", '')[:20]

CATEGORIES = {'alt': 'Alternative', 'oscar': 'Oscar Nominee', 'classic': 'Classic'}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Add a film to films.json')
    parser.add_argument('title', help='Film title to look up')
    parser.add_argument('--year', '-y', help='Release year (helps find the right film)')
    args = parser.parse_args()

    print(f"Looking up \"{args.title}\"...\n")
    film = search_film(args.title, args.year)
    if not film:
        sys.exit(1)

    # Display what we found
    print(f"  Title:    {film['Title']} ({film['Year']})")
    print(f"  Director: {film.get('Director', 'N/A')}")
    print(f"  Runtime:  {film.get('Runtime', 'N/A')}")
    print(f"  Genre:    {film.get('Genre', 'N/A')}")
    print(f"  Plot:     {film.get('Plot', 'N/A')}")
    print()

    # Ask: screening or candidate?
    print("Add as:")
    print("  1. Scheduled screening")
    print("  2. Voting candidate")
    print("  0. Cancel")
    choice = input("\nChoice: ").strip()

    if choice == '0':
        print("Cancelled.")
        return

    data = load_films()
    film_id = make_id(film['Title'])
    runtime = film.get('Runtime', 'N/A')
    director = film.get('Director', 'N/A')
    year = film.get('Year', '').split('–')[0]  # handle ranges like "2023–2024"
    genre = film.get('Genre', 'N/A')
    synopsis = film.get('Plot', '')

    if choice == '1':
        # Scheduled screening
        print("\nCategory:")
        for k, v in CATEGORIES.items():
            print(f"  {k} = {v}")
        cat = input("Category [alt/oscar/classic]: ").strip() or 'alt'

        date = input("Screening date (e.g. Sat 1 Mar): ").strip()
        time = input("Screening time [6:30 PM]: ").strip() or '6:30 PM'

        entry = {
            "id": film_id,
            "title": film['Title'],
            "year": int(year) if year.isdigit() else year,
            "director": director,
            "runtime": runtime,
            "genre": genre,
            "category": cat,
            "synopsis": synopsis,
            "date": date,
            "time": time,
            "trailer": f"https://www.youtube.com/results?search_query={urllib.parse.quote(film['Title'])}+trailer"
        }
        data['films'].append(entry)
        save_films(data)
        print(f"\nAdded \"{film['Title']}\" to scheduled screenings.")

    elif choice == '2':
        entry = {
            "id": f"c{len(data.get('candidates', [])) + 1}",
            "title": film['Title'],
            "info": f"{year} · {director} · {runtime}"
        }
        data.setdefault('candidates', []).append(entry)
        save_films(data)
        print(f"\nAdded \"{film['Title']}\" to voting candidates.")

    else:
        print("Cancelled.")

if __name__ == '__main__':
    main()
