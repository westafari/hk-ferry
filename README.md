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
This is a personal project. Only the owner can push; pull requests and issues from others are switched off.
