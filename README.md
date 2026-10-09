# HK Ferry Times

An offline-capable phone page with Hong Kong ferry timetables, adult fares, and a "Going to…" view that shows the next boats out and your return options.

- Harbour, outlying-island and Lantau routes: built from the Transport Department's open timetable CSVs (`build.py` downloads them).
- Star Ferry: frequency bands (it has no fixed timetable), typed in `src/make_data.py`.
- Kaito (small ferries): typed in `src/make_data.py` from the Transport Department's kaito page. Re-check these by hand now and then.
- Crossing times marked `approx` in `src/make_data.py` are estimates, not from the source data.

## Use on iPhone
Open the site in Safari, tap Share, then Add to Home Screen. After the first load it works with no signal.

## Develop
    python3 build.py              # download data and build public/index.html
    python3 build.py --no-fetch   # rebuild from td/
    python3 tools/make_icons.py   # redraw the icons

GitHub Actions rebuilds and deploys to GitHub Pages on every push and weekly. If a download fails or looks wrong, the build stops and the last good site stays up.

## Contributing
Pull requests and issues are welcome. Only the owner can merge, and every change needs approval before it reaches `main`.

Good things to send:
- **Timetable corrections.** Say which route, which day type, and where you saw the right time (operator site, a photo of the pier notice).
- **Kaito and Star Ferry data.** These are typed by hand in `src/make_data.py` and are the most likely to be wrong or stale.
- **Pier pins.** Piers marked "approximate pin" or "no map pin" in `src/make_data.py` need a verified coordinate.
- **Crossing times** marked `approx`.

Run `python3 build.py --no-fetch` and open `public/index.html` to check your change. The timetables themselves come from the Transport Department's open data, so fix those at the source, not in a pull request.
