library(circlize)

# set directory
setwd('~/OneDrive - Nexus365/local/OMS/analysis/plots')

# read data
df <- read.csv(file = 'test_chord.csv')

# chord
chordDiagram(df)

# Restart circular layout parameters
circos.clear()