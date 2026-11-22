# v2 shot list: (out_start, out_end, source_prefix, source_in, flags)
# flags: zoom (100->105%), photo, crop=(cx, cy, factor) in rotated-source pixels, nat=section gain override
# Beat grid 96 BPM (0.625 s) from 4.0 s. Hook PAPs at 0.0 / 0.7 / 1.4. Reveal (bass hit) at 38.0.
SHOTS = [
    # HOOK - three PAP hard cuts
    (0.000,  0.700, "IMG_1523__1_lQr3", 0.2,  {"crop": (1600, 2050, 2.6), "nat": 1.0}),   # PAP1 hand + rope + harness
    (0.700,  1.400, "IMG_1365__1_bbut", 0.0,  {"crop": (1150, 3300, 2.4), "nat": 1.3}),   # PAP2 boots on rock, scrape
    (1.400,  4.000, "IMG_0001__1IHO3E", 7.0,  {"zoom": True, "nat": 0.9}),                # PAP3 ridge + drop, hold
    # REWIND - condensed journey
    (4.000,  5.250, "IMG_0981__10FJzc", 0.3,  {"nat": 0.25}),   # Malaysia (KLIA)
    (5.250,  6.500, "IMG_1020__14_5Oo", 2.0,  {"nat": 0.25}),   # ride to basecamp
    (6.500,  7.750, "IMG_0999__18s3YJ", 0.0,  {"photo": True}), # Basecamp Mas Bagus
    (7.750,  9.000, "IMG_1706__1YJDRZ", 0.0,  {"nat": 0.25}),   # trail gate
    # CLIMB TO CP7 - drums come in
    (9.000, 10.250, "IMG_1050__1v1yCY", 1.0,  {"nat": 0.35}),   # wide forest climb
    (10.250,11.500, "IMG_1204__1LAqhw", 9.0,  {"nat": 0.35}),   # close hand on roots
    (11.500,12.750, "IMG_1196__1GXQ8b", 2.2,  {"nat": 0.35}),   # close boots
    (12.750,14.000, "IMG_1196__1GXQ8b", 10.0, {"nat": 0.35}),   # wide fog giants
    (14.000,15.250, "IMG_1111__1Mxbb3", 0.0,  {"photo": True}), # rest in fog
    (15.250,16.500, "IMG_1204__1LAqhw", 0.3,  {"nat": 0.35}),   # low angle giant tree
    (16.500,17.750, "IMG_1525__1pHQuE", 0.5,  {"nat": 0.35}),   # CP7 camp
    (17.750,19.000, "IMG_1243__1BXB13", 10.0, {"nat": 0.35}),   # sunset
    (19.000,20.250, "IMG_1248__1DKKH4", 0.5,  {"nat": 0.35}),   # sunset silhouette
    (20.250,21.500, "IMG_1305__1E3s6P", 2.0,  {"nat": 0.35}),   # sunrise 04:57
    (21.500,22.750, "IMG_1286__1A3L3M", 5.0,  {"nat": 0.5}),    # summit push
    # ROPE + RIDGE - close -> wide pairs, real order (06:19 -> 06:56)
    (22.750,24.000, "IMG_9982__1Nhlqu", 9.5,  {"crop": (900, 1700, 1.8), "nat": 0.75}),  # close: hands/feet on wall
    (24.000,26.500, "IMG_1350__17_c0I", 6.0,  {"nat": 0.6}),    # wide: the wall
    (26.500,27.750, "IMG_1365__1_bbut", 4.0,  {"crop": (950, 2100, 1.6), "nat": 0.75}),  # close: hand on fixed rope
    (27.750,30.250, "IMG_1364__1n-y1h", 1.0,  {"nat": 0.6}),    # wide: rope line, peak behind
    (30.250,31.500, "IMG_0001__1aVWTJ", 12.5, {"crop": (1300, 2500, 2.0), "nat": 0.75}), # close: feet on knife edge
    (31.500,34.000, "IMG_1372__1Y-z31", 13.5, {"nat": 0.7}),    # wide: ridge + drop, HOLD 2.5 s
    (34.000,36.250, "IMG_1389__1YoxPk", 0.0,  {"nat": 0.8}),    # walking to the rim
    (36.250,38.000, "IMG_0026__1MKMcW", 0.0,  {"nat": 0.45}),    # summit sign; music silent 37.5-38.0
    # REVEAL
    (38.000,44.000, "IMG_0026__1MKMcW", 4.3,  {"zoom": True, "nat": 0.2}),  # crater fills screen, BASS HIT + title
    (44.000,46.000, "IMG_1399__1oszLD", 0.0,  {"nat": 0.3}),    # arms up over the crater
    (46.000,48.500, "IMG_0056__1mvQMZ", 12.6, {"nat": 0.3}),    # on the summit spires
    # DESCENT - abseil in true order (13:00)
    (48.500,49.750, "IMG_0089__1siVRf", 4.5,  {"crop": (918, 1650, 1.8), "nat": 0.7}),  # close: hands on rope
    (49.750,52.500, "IMG_1523__1_lQr3", 28.0, {"nat": 0.6}),    # wide: abseil down the gully
    (52.500,55.000, "IMG_0122__1PlD-_", 21.0, {"nat": 0.35}),   # descent, day 3
    (55.000,57.500, "IMG_1706__1YJDRZ", 5.0,  {"nat": 0.35}),   # back out through the gate
    (57.500,60.000, "IMG_0981__10FJzc", 9.5,  {"nat": 0.45}),   # back to KLIA -> Day 1
]
