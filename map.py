import numpy as np
import os, math
import sys

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QPushButton

import pyqtgraph as pg
from PIL import Image, ImageDraw


class Map(QMainWindow):

    def __init__(self):
        super().__init__()
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.invertY()
        self.graphWidget.setAspectLocked()
        self.graphWidget.setBackground('w')
        self.graphWidget.getPlotItem().hideAxis('bottom')
        self.graphWidget.getPlotItem().hideAxis('left')
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle("Map Display")

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.latlon = QLineEdit(self)
        self.latlon.setFixedWidth(270)
        self.latlon.setPlaceholderText("1.34047, 103.70935 (latitude, longtitude)")
        self.latlon.move(5,5)
        self.horizontalLayout.addWidget(self.latlon, alignment=QtCore.Qt.AlignCenter)

        self.pb = QPushButton(self)
        self.pb.setText("Update GPS")
        self.pb.move(280, 5)
        self.pb.clicked.connect(lambda: self.getImageCluster(self.latlon.text()))
        self.horizontalLayout.addWidget(self.pb)

        self.zoom_level = 15
        self.x_list = list()
        self.y_list = list()
        self.location_point = None

        self.getImageCluster("1.34047, 103.70935")
        self.show()

    def deg2num_float(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x_float = float((lon_deg + 180.0) / 360.0 * n)
        y_float = float((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (x_float, y_float)

    # latitude and longtitude to tile numbers
    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    def getImageCluster(self, latlon_deg, delta_lat=0.02,  delta_long=0.02):

        latlon_deg = latlon_deg.split(',')
        lat_deg = latlon_deg[0].replace(" ", "")
        lon_deg = latlon_deg[1].replace(" ", "")

        self.x_list.clear()
        self.y_list.clear()

        try:
            lat_deg = float(lat_deg)
            lon_deg = float(lon_deg)
        except ValueError:
            print("Invalid longtitude and latitude!")
            return

        smurl = '{0}/{1}/{2}.png'

        self.xmin, self.ymax = self.deg2num(lat_deg - delta_lat, lon_deg - delta_long, self.zoom_level)
        self.xmax, self.ymin = self.deg2num(lat_deg + delta_lat, lon_deg + delta_long, self.zoom_level)

        Cluster = Image.new('RGB',((self.xmax-self.xmin+1)*256-1, (self.ymax-self.ymin+1)*256-1))

        for xtile in range(self.xmin, self.xmax+1):
            for ytile in range(self.ymin, self.ymax+1):
              imgurl = smurl.format(self.zoom_level, xtile, ytile)

              if not os.path.exists(imgurl):
                print("Invalid longtitude and latitude!")
                return

              if xtile not in self.x_list:
                self.x_list.append(xtile)
              if ytile not in self.y_list:
                self.y_list.append(ytile)

              tile = Image.open(imgurl)
              Cluster.paste(tile, box=((xtile-self.xmin)*256, (ytile-self.ymin)*256))

        img = pg.ImageItem(np.asarray(Cluster), axisOrder='row-major')
        self.graphWidget.addItem(img)
        self.graphWidget.setLimits(xMin=0, xMax=5*256, yMin=0, yMax=5*256)

        self.updateCoordinate(lat_deg, lon_deg)

    def updateCoordinate(self, lat, lon):
        if self.location_point is not None:
            self.graphWidget.removeItem(self.location_point)



        x, y = self.deg2num_float(lat, lon, self.zoom_level)

        x_pixel = (x % 1)*256
        y_pixel = (y % 1)*256

        x_index = self.x_list.index(int(x))
        y_index = self.y_list.index(int(y))

        new_x = (256*x_index) + x_pixel
        new_y = (256*y_index) + y_pixel

        # setup location point
        self.location_point = pg.QtGui.QGraphicsPixmapItem(pg.QtGui.QPixmap('marker-icon-red.png'))
        self.location_point.setPos(new_x-(self.location_point.boundingRect().width()/2), new_y-self.location_point.boundingRect().height())
        self.graphWidget.addItem(self.location_point)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = Map()
    sys.exit(app.exec_())