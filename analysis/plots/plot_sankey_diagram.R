library(circlize)
library(networkD3)
library(dplyr)

# set directory
setwd('~/OneDrive - Nexus365/local/OMS/analysis/plots')

colors <- c(ISR = '#537BEF',
            GZA = '#FFC50F',
            WBK = '#F43D3D',
            EGY = 'black',
            JOR = '#27B02B')

scenario = 'COO'
df <- read.csv(file = paste('chord_data/',scenario,'.csv',sep=''))

# A connection data frame is a list of flows with intensity for each flow
links <- df

# From these flows we need to create a node data frame: it lists every entities involved in the flow
nodes <- data.frame(
  name=c(as.character(links$from_territory), 
         as.character(links$to_territory)) %>% unique()
)

# With networkD3, connection must be provided using id, not using real name like in the links dataframe.. So we need to reformat it.
links$IDsource <- match(links$from_territory, nodes$name)-1 
links$IDtarget <- match(links$to_territory, nodes$name)-1

node_colour <- 'd3.scaleOrdinal().domain(["EGY_SUPPLY", 
                                          "GZA_SUPPLY",
                                          "GZA_DEMAND", 
                                          "ISR_SUPPLY", 
                                          "ISR_DEMAND", 
                                          "JOR_SUPPLY", 
                                          "JOR_DEMAND", 
                                          "WBK_SUPPLY", 
                                          "WBK_DEMAND",]).range(["black",
                                                                "#FFC50F" ,
                                                                "#FFC50F", 
                                                                "#537BEF", 
                                                                "#537BEF", 
                                                                "#27B02B", 
                                                                "#27B02B", 
                                                                "#F43D3D",
                                                                "#F43D3D"])'


edge_colour <- 'd3.scaleOrdinal().domain(["type_a",
                                          "type_b",
                                          "my_unique_group"]).range(["#69b3a2",
                                                                     "steelblue",
                                                                     "grey"])'


# Make the Network
p <- sankeyNetwork(Links = links, 
                   Nodes = nodes,
                   Source = "IDsource", 
                   Target = "IDtarget",
                   Value = "value", 
                   NodeID = "name", 
                   height = 600,
                   width = 1100,
                   fontFamily = 'Arial',
                   fontSize = 14,
                   units = 'kWh',
                   nodePadding = 20,
                   nodeWidth = 15,
                   colourScale=my_color,
                   sinksRight=FALSE)

p