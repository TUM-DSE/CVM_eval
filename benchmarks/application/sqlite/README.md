- SQLite's [kvtest](https://www.sqlite.org/src/file/test/kvtest.c)

## Run
```
nix-shell
just init # this creates db file (~2GB) in ./data

just run_seq
just run_rand
just run_update
just run_update_rand
```

