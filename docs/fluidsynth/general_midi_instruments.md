# General MIDI Instrument Program Numbers

Reference for FluidSynth instrument selection and program changes.

## Key Orchestral Instruments

| Instrument | Program Number | MIDI Command |
|------------|----------------|--------------|
| **Piano** |
| Acoustic Grand Piano | 1 | `--prog 0 1` |
| Bright Acoustic Piano | 2 | `--prog 0 2` |
| Electric Grand Piano | 3 | `--prog 0 3` |
| **Strings** |
| Violin | 41 | `--prog 0 41` |
| Viola | 42 | `--prog 0 42` |
| Cello | 43 | `--prog 0 43` |
| Contrabass | 44 | `--prog 0 44` |
| String Ensemble 1 | 49 | `--prog 0 49` |
| String Ensemble 2 | 50 | `--prog 0 50` |
| **Woodwinds** |
| Flute | 74 | `--prog 0 74` |
| Piccolo | 73 | `--prog 0 73` |
| Recorder | 75 | `--prog 0 75` |
| Pan Flute | 76 | `--prog 0 76` |
| Clarinet | 72 | `--prog 0 72` |
| Oboe | 69 | `--prog 0 69` |
| **Brass** |
| Trumpet | 57 | `--prog 0 57` |
| Trombone | 58 | `--prog 0 58` |
| French Horn | 61 | `--prog 0 61` |
| Tuba | 59 | `--prog 0 59` |

## Complete General MIDI Instrument List (1-128)

### Piano (1-8)
1. Acoustic Grand Piano
2. Bright Acoustic Piano
3. Electric Grand Piano
4. Honky-tonk Piano
5. Rhodes Piano
6. Chorused Piano
7. Harpsichord
8. Clavinet

### Chromatic Percussion (9-16)
9. Celesta
10. Glockenspiel
11. Music Box
12. Vibraphone
13. Marimba
14. Xylophone
15. Tubular Bells
16. Dulcimer

### Organ (17-24)
17. Hammond Organ
18. Percussive Organ
19. Rock Organ
20. Church Organ
21. Reed Organ
22. Accordion
23. Harmonica
24. Tango Accordion

### Guitar (25-32)
25. Acoustic Guitar (nylon)
26. Acoustic Guitar (steel)
27. Electric Guitar (jazz)
28. Electric Guitar (clean)
29. Electric Guitar (muted)
30. Overdriven Guitar
31. Distortion Guitar
32. Guitar Harmonics

### Bass (33-40)
33. Acoustic Bass
34. Electric Bass (finger)
35. Electric Bass (pick)
36. Fretless Bass
37. Slap Bass 1
38. Slap Bass 2
39. Synth Bass 1
40. Synth Bass 2

### Strings (41-48)
41. Violin
42. Viola
43. Cello
44. Contrabass
45. Tremolo Strings
46. Pizzicato Strings
47. Orchestral Harp
48. Timpani

### Ensemble (49-56)
49. String Ensemble 1
50. String Ensemble 2
51. Synth Strings 1
52. Synth Strings 2
53. Choir Aahs
54. Voice Oohs
55. Synth Voice
56. Orchestra Hit

### Brass (57-64)
57. Trumpet
58. Trombone
59. Tuba
60. Muted Trumpet
61. French Horn
62. Brass Section
63. Synth Brass 1
64. Synth Brass 2

### Reed (65-72)
65. Soprano Sax
66. Alto Sax
67. Tenor Sax
68. Baritone Sax
69. Oboe
70. English Horn
71. Bassoon
72. Clarinet

### Pipe (73-80)
73. Piccolo
74. Flute
75. Recorder
76. Pan Flute
77. Blown Bottle
78. Shakuhachi
79. Whistle
80. Ocarina

### Synth Lead (81-88)
81. Lead 1 (square)
82. Lead 2 (sawtooth)
83. Lead 3 (calliope)
84. Lead 4 (chiff)
85. Lead 5 (charang)
86. Lead 6 (voice)
87. Lead 7 (fifths)
88. Lead 8 (bass + lead)

### Synth Pad (89-96)
89. Pad 1 (new age)
90. Pad 2 (warm)
91. Pad 3 (polysynth)
92. Pad 4 (choir)
93. Pad 5 (bowed)
94. Pad 6 (metallic)
95. Pad 7 (halo)
96. Pad 8 (sweep)

### Synth Effects (97-104)
97. FX 1 (rain)
98. FX 2 (soundtrack)
99. FX 3 (crystal)
100. FX 4 (atmosphere)
101. FX 5 (brightness)
102. FX 6 (goblins)
103. FX 7 (echoes)
104. FX 8 (sci-fi)

### Ethnic (105-112)
105. Sitar
106. Banjo
107. Shamisen
108. Koto
109. Kalimba
110. Bag pipe
111. Fiddle
112. Shanai

### Percussive (113-120)
113. Tinkle Bell
114. Agogo
115. Steel Drums
116. Woodblock
117. Taiko Drum
118. Melodic Tom
119. Synth Drum
120. Reverse Cymbal

### Sound Effects (121-128)
121. Guitar Fret Noise
122. Breath Noise
123. Seashore
124. Bird Tweet
125. Telephone Ring
126. Helicopter
127. Applause
128. Gunshot

## FluidSynth Commands

### Basic Program Change
```bash
# Select flute (program 74) on channel 0
fluidsynth -ni soundfont.sf2 --prog 0 74 midifile.mid

# Select violin (program 41) on channel 0
fluidsynth -ni soundfont.sf2 --prog 0 41 midifile.mid
```

### Multiple Instruments
```bash
# Channel 0: Flute, Channel 1: Violin
fluidsynth -ni soundfont.sf2 \
  --prog 0 74 \
  --prog 1 41 \
  midifile.mid
```

### Interactive Commands
In FluidSynth interactive mode:
```
> prog 0 74    # Channel 0 to Flute
> prog 1 41    # Channel 1 to Violin
```

## Instrument Mapping for Sib2Ae

Based on our project's instrument names, here's the mapping:

| Sib2Ae Name | General MIDI | Program # |
|-------------|--------------|-----------|
| Flûte       | Flute        | 74        |
| Violon      | Violin       | 41        |
| Piano       | Acoustic Grand Piano | 1 |
| Viola       | Viola        | 42        |
| Cello       | Cello        | 43        |
| Contrebasse | Contrabass   | 44        |

## References

- [FluidSynth API Documentation](https://www.fluidsynth.org/api/)
- [General MIDI Specification](https://en.wikipedia.org/wiki/General_MIDI)
- [MIDI Program Change Messages](https://www.midi.org/specifications-old)