library(mapview)
library(htmlwidgets)
library(sf)
library(leafem)
library(leaflet)

dirpath = setwd('/Users/amanmajid/OneDrive - Nexus365/local/OMS/')

# Load shapefiles
water_bodies = read_sf(paste(dirpath,'/data/spatial/water-basins.shp',sep=''))
electricity = read_sf(paste(dirpath,'/oms-web-portal/layer-data/electricity-lines.shp',sep=''))
density = read_sf(paste(dirpath,'/data/spatial/population-density-cropped.shp',sep=''))

# write a function to remove all zoom to calls
#   use the Filter above but change == to !=
remove_zoomto <- function(leafmap) {
  if(inherits(leafmap, "mapview")) {
    leafmap <- leafmap@map
  }
  
  leafmap$x$calls <- Filter(
    function(cl) {
      cl$method != "addHomeButton"
    },
    leafmap$x$calls
  )
  
  leafmap
}

# map
m = remove_zoomto(
    mapview(
      water_bodies,
      zcol='Name',
      legend = FALSE,
      layer.name='Water Basins'
      ) + mapview(
            electricity,
            zcol='nat.graphi',
            color='red',
            hide = TRUE,
            legend = FALSE,
            layer.name='Electricity lines'
            ))


m = leafem::addLogo(m, 
                   "https://raw.githubusercontent.com/amanmajid/nextra/main/data/_raw/OMS-sq-quad-rgb.jpg", 
                    url = "https://www.oxfordmartin.ox.ac.uk/transboundary-resource-management",
                    position = 'bottomright',
                    offset.x = 10,
                    offset.y = 20,
                    width = 150,
                    height = 75)


m

mapshot(m, 
        url = paste0(getwd(), "/oms-web-portal/packaged/index.html"),
        title="OMS MENA")