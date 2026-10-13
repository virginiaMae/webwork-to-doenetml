# webwork-to-doenetml

Working materials for converting WeBWorK problems to
[DoenetML](https://www.doenet.org), plus local mirrors of the converted
course content on doenet.org.

| Folder | What's in it |
| --- | --- |
| `umtymp-calculus1-f26/` | Mirror of the UMTYMP Calculus 1 (Fall 2026) folder on doenet.org, kept in sync with `scripts/` (see below) |
| `Webwork2DoenetML/` | Raw WeBWorK `.pl` homework problems used as converter inputs |
| `DoenetML-output/` | Sample converter output |
| `Perl to DoenetML/` | An early Python converter (`perl_to_doenetml.py`), superseded by the JS converter |
| `scripts/` | Pull/push sync with doenet.org |

The converter itself lives in the DoenetML monorepo at
[`packages/webwork-to-doenetml/`](https://github.com/Doenet/DoenetML/tree/main/packages/webwork-to-doenetml).

## Syncing with doenet.org

Any folder here that contains a `doenet-sync.json` mirrors one folder on
doenet.org:

```
{
  "folderId": "kP4hWuV6gEEfpWrhmVjEYa",
  "ownerId": "pcKKBXm3cunporFKSGZD5D"
}
```

Both IDs are in the folder's doenet.org URL:
`https://doenet.org/sharedActivities/<ownerId>/<folderId>`. The scripts
use only the Python standard library.

### Setup

```
cp .env.example .env
# then paste a fresh connect.sid cookie value into .env (see .env.example)
```

The cookie must belong to the account that owns the folder. `.env` is
gitignored; never commit it.

### Pull

Creates new files, updates existing ones in place, and never overwrites a
file you've edited locally but haven't pushed yet:

```
python3 scripts/doenet_pull.py                              # every synced folder
python3 scripts/doenet_pull.py --root umtymp-calculus1-f26  # just one
python3 scripts/doenet_pull.py --dry-run                    # preview only
```

### Edit

Each pulled `.doenetml` file starts with a tool-managed block:

```
<!-- Doenet-Sync
Doenet-Sync-ID: mWJ7coDgf2wJRdKhHo3k48
Doenet-Sync-Version: 0.7.28
Doenet-Sync-NumVariants: 100
Doenet-Sync-Hash: a5fc847e18652f89
-->
```

Don't hand-edit it. Everything below it is normal editing territory. The
block only exists locally and is never sent to doenet.org.

### Push

```
python3 scripts/doenet_push.py path/to/activity.doenetml
python3 scripts/doenet_push.py --all              # every changed file
python3 scripts/doenet_push.py --all --dry-run    # preview
```

Before overwriting an activity, push re-checks it on doenet.org. If it
changed since your last pull/push, that file is skipped with a `CONFLICT`
message: pull first, or re-run push with `--force` to overwrite anyway.

### Limitations

- Only individual activities are mirrored. Problem sets on doenet.org hold
  their own copies of activities, which pushing from here does not update.
- `numVariants` is carried over as-is on push, not recomputed. If an edit
  changes how many variants an activity generates, check the count in the
  Doenet editor afterward.
- New activities have to be created on doenet.org first, then pulled.
