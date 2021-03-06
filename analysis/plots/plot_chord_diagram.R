library(circlize)

# set directory
setwd('~/OneDrive - Nexus365/local/OMS/analysis/plots')

colors <- c(ISR = '#537BEF',
            GZA = '#FFC50F',
            WBK = '#F43D3D',
            EGY = 'black',
            JOR = '#27B02B')

for (scenario in c('NCO','COO','EAG','BAU')) #,'UTO'
{
  print(paste('> Running:', scenario))
  df <- read.csv(file = paste('chord_data/',scenario,'.csv',sep=''))
  
  # open pdf
  pdf( paste('../../outputs/figures/',scenario,'.pdf',sep='') )
    
  circos.par(start.degree = 85, clock.wise = TRUE)
  circos.par(gap.after = c('ISR' = 10))    
  
  chordDiagram(df,
               grid.col=colors,
               link.lwd = 0.5,    # Line width
               link.lty = 0,    # Line type
               link.border = 1,
               directional = 1,
               direction.type = c("arrows", "diffHeight"), 
               #diffHeight  = -0.04,
               #annotationTrack = "grid", 
               annotationTrackHeight = c(0.1, 0.1),
               link.arr.type = "big.arrow", 
               #link.sort = TRUE, 
               #link.largest.ontop = TRUE,
               transparency = 0.6)

  title(main = scenario)
  
  # Restart circular layout parameters
  circos.clear()
  
  dev.off() 
  
}
 

