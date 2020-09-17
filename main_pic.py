import configparser
import shutil

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import sys
import time
import json
import csv
import pandas as pd
import copy

colors=['(0,255,0)','(255,0,0)','(0,0,255)','(255,255,0)','(255,0,255)','(0,255,255)','(22,7,201)']
colors_2=[(0,255,0),(255,0,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255),(22,7,201),(30,144,255),(0,139,0),(192,255,62)
    ,(255,255,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(22,7,201),(30,144,255),(0,139,0),(192,255,62)]

class McrollArea(QScrollArea):

    def __init__(self,parent):
        QScrollArea.__init__(self,parent)
        self.mainUI=parent

    def wheelEvent(self, event):
        super().wheelEvent(event)

        if not os.path.isfile('classes.csv'):
            with open('classes.csv', 'w', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                ## 目标： 不需要hard coded
                columns = copy.deepcopy(self.mainUI.cls_1) 
                columns.insert(0,'image')
                csv_writer.writerow(columns)

        df = pd.read_csv('classes.csv')
 
     
        if (not self.mainUI.key_shift) and (not self.mainUI.key_control) and (not self.mainUI.key_del) and (not self.mainUI.negative_flag) and len(self.mainUI.will_changes) > 0:
            for will_weight in self.mainUI.will_changes:
                i = len(df) + 1
                if os.path.exists(will_weight.image_path):
                    # save_dir=self.mainUI.get_save_dir()
                    # print(save_dir)
                    # will_weight.out_path = save_dir + "/" + os.path.basename(will_weight.image_path)
                    # print(will_weight.out_path)
                    # cls_label = will_weight.out_path.split('/')[-2]
                    # print(will_weight.image_path)
                    # print(cls_label)
                    cls_label = self.mainUI.get_class()
                    df.loc[i] = [os.path.relpath(will_weight.image_path), 0, 0, 0, 0, 0]
                    df.loc[(df.image == os.path.relpath(will_weight.image_path)), cls_label] = 1
                    df.drop_duplicates(subset=['image'] ,keep='first', inplace=True)
                    # will_weight.image_path=will_weight.out_path
                    will_weight.deleteLater()
            self.mainUI.will_changes.clear()

        if self.mainUI.key_del and len(self.mainUI.will_changes) > 0:
            for will_weight in self.mainUI.will_changes:
                if os.path.exists(will_weight.image_path):
                    os.makedirs('del', exist_ok=True)
                    # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
                    will_weight.out_path = 'del' + "/" + os.path.basename(will_weight.image_path)
                    shutil.move(will_weight.image_path,  will_weight.out_path)
                    # print(will_weight.image_path)
                    df.drop(df[df.image == os.path.relpath(will_weight.image_path)].index, inplace=True)
                    will_weight.deleteLater()
                    self.mainUI.key_del = False
                    self.mainUI.key_label.setText("key:none   ")
            self.mainUI.will_changes.clear()


        ##负样本功能###
        if self.mainUI.negative_flag and len(self.mainUI.will_changes) > 0:
            for will_weight in self.mainUI.will_changes:
                # save_dir=self.mainUI.get_save_dir()
                # will_weight.out_path = save_dir + "/" + os.path.basename(will_weight.image_path)
                # print(will_weight.out_path)
                # cls_label = will_weight.out_path.split('/')[-2]
                cls_label = self.mainUI.get_class()
                df.loc[(df.image == os.path.relpath(will_weight.image_path)), cls_label] = 0
                will_weight.deleteLater()
                self.mainUI.negative_flag = False
            self.mainUI.will_changes.clear()
        df.to_csv('classes.csv', index=False)

        if self.mainUI.edit_mode != 0:
            if self.mainUI.gridLayout.count()==0 and self.mainUI.next_page.isEnabled():
                self.mainUI.open_next()
        # if self.verticalScrollBar().value()%self.parent().height>0:
        #     print("next",self.verticalScrollBar().value()%self.parent().height)
        # print('wheelEvent',self.verticalScrollBar().value(),self.parent().pic_count,self.parent().get_grid_cols(),self.parent().pic_count//self.parent().get_grid_cols())


class Img_viewed(QMainWindow):
    _signal=QtCore.pyqtSignal(str)
    def __init__(self,parent =None):
        super(Img_viewed, self).__init__(parent)
        self.parent = parent
        self.width = 1920
        self.height =1080-70
        self.setWindowTitle('cls label')
        self.resize(self.width,self.height)
        ## read config file 
        self.jimi_config = configparser.ConfigParser()
        self.config_file_path = 'label_config.ini'
        self.jimi_config.read(self.config_file_path)
        self.cls_1= self.jimi_config.get("cls", "1").split(",")  ## return list of classes
        self.cls_2= self.jimi_config.get("cls", "2").split(",")
        self.save_dir= self.jimi_config.get("cls", "save_dir")   ## return str of saving dir
        self.pic_width= self.jimi_config.getint("default", "pic_width")
        if len(self.cls_1)==0:
            QMessageBox.warning(self, '错误', 'label_config cls 1不能为空')
            exit(1)
            
        self.scroll_ares_images = McrollArea(self)
        self.scroll_ares_images.setWidgetResizable(True)

        self.scrollAreaWidgetContents = QWidget(self)
        self.scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContends')

        # 进行网络布局
        # self.scroll_ares_images.wheelEvent()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setSpacing(1)
        self.gridLayout.setContentsMargins(1,1,1,1)
        self.scroll_ares_images.setWidget(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.gridLayout)
        self.scroll_ares_images.setGeometry(10, 50, self.width-30, self.height-80)
        self.get_statusBar()

        # self.meanbar = QMenu(self)
        # self.meanbar.addMenu('&菜单')
        # self.openAct = self.meanbar.addAction('&Open',self.open)
        # self.startAct =self.meanbar.addAction('&start',self.start_img_viewer)
        self.open_file_pushbutton =QPushButton(self)
        self.open_file_pushbutton.setGeometry(20,10,100,30)
        self.open_file_pushbutton.setObjectName('open_pushbutton')
        self.open_file_pushbutton.setText('打开文件夹')
        self.open_file_pushbutton.clicked.connect(self.open)

        self.label_cls1 = QLabel(self)
        self.label_cls1.setText("☆一级:")
        self.label_cls1.setGeometry(150 + 150-40 , 10, 50, 30)
        for index, cls_name in enumerate(self.cls_1):
            start_file_pushbutton = QPushButton(self)
            start_file_pushbutton.setGeometry(150+150+index*82, 10, 80, 30)
            start_file_pushbutton.setObjectName('cls1_'+str(index))
            start_file_pushbutton.setText(cls_name)
            start_file_pushbutton.clicked.connect(self.select_cls)
        
        self.del_file_pushbutton = QPushButton(self)
        self.del_file_pushbutton.setGeometry(750, 10, 80, 30)
        self.del_file_pushbutton.setObjectName('del')
        self.del_file_pushbutton.setText('delete')
        self.del_file_pushbutton.clicked.connect(self.delete)

        self.cb = QComboBox(self)
        self.cb.setGeometry(1000,10,100,30)
        # self.cb.addItem("C")                                       # 添加一个项目
        self.cb.addItems(["blur", "nonblur"])                 # 添加多个项目
        self.cb.currentIndexChanged.connect(self.changeIndex)  # 发射currentIndexChanged信号，连接下面的selectionchange槽

        # self.label_cls1 = QLabel(self)
        # self.label_cls1.setText("☆二级:")
        # self.label_cls1.setGeometry(150 + 150 +80+ (len(self.cls_1)) * 82-40, 10, 50, 30)
        # for index, cls_name in enumerate(self.cls_2):
        #     start_file_pushbutton = QPushButton(self)
        #     start_file_pushbutton.setGeometry(150 + 150 +80+ (len(self.cls_1)+index) * 82, 10, 80, 30)
        #     start_file_pushbutton.setObjectName('cls2_'+str(index))
        #     start_file_pushbutton.setText(cls_name)
        #     start_file_pushbutton.clicked.connect(self.select_cls)

        self.change_mode_pushbutton = QPushButton(self)
        self.change_mode_pushbutton.setGeometry(150, 10, 100, 30)
        self.change_mode_pushbutton.setObjectName('start')
        self.change_mode_pushbutton.setText('点切标注模式')
        self.change_mode_pushbutton.clicked.connect(self.start_img_viewer)

        self.positive_pushbutton = QPushButton(self)
        self.positive_pushbutton.setGeometry(150 + 150 +80+ (len(self.cls_1)) * 100, 10, 50, 30)
        self.positive_pushbutton.setObjectName('positive')
        self.positive_pushbutton.setText('正样本')
        self.positive_pushbutton.clicked.connect(self.select_positve)

        self.negative_pushbutton = QPushButton(self)
        self.negative_pushbutton.setGeometry(150 + 150 +80+ (len(self.cls_1)) * 110, 10, 50, 30)
        self.negative_pushbutton.setObjectName('negative')
        self.negative_pushbutton.setText('负样本')
        self.negative_pushbutton.clicked.connect(self.select_negative)

        self.vertocal = QVBoxLayout()
        self.vertocal.addWidget(self.scroll_ares_images)
        self.show()
        #设置图片的预览尺寸；
        self.displayed_image_size = self.pic_width
        self.page_count = 18 * 9 * 3
        self.col = 0
        self.row =0

        self.initial_path = self.jimi_config.get("default", "last_dir")

        self.m_drag=False
        self.init_data()

    def init_data(self):

        self.last_cls=None
        self.cls_index_1=-1
        self.cls_index_2=-1
        self.cls_level=None

        self.key_shift=False
        self.key_control=False
        self.key_del=False
        self.negative_flag=False
        

        self.grid_index_last=-1
        self.page_index=-1
        self.will_changes=[]

    def open_next(self):

        self.key_shift = False
        self.key_control = False
        self.key_del = False
        self.negative_flag=False
        self.grid_index_last = -1
        self.will_changes = []
        self.page_index += 1

        for i in range(self.page_count):
            willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
            if willselect is None:
                continue
            else:
                willselect.deleteLater()
        if self.img_total<=self.page_index*self.page_count:
            self.next_page.setEnabled(False)

        else:
            self.next_page.setEnabled(True)
        tabel_datas = self.img_files[self.page_count*(self.page_index-1):self.page_count*self.page_index]

        self.pic_count = len(tabel_datas)

        self.label_path.setText(f"共:{self.img_total}条 当前{self.page_index} 页 共 {self.img_total//self.page_count+1} 页 路径:")
        pic_of_columns = self.get_grid_cols()

        # print(self.pic_count, pic_of_columns, self.pic_count // pic_of_columns + 1)
        if self.pic_count != 0:
            for i in range(self.pic_count):
                image_path = tabel_datas[i]
                pixmap = QPixmap(image_path)
                self.addImage(i, pixmap, image_path)

    def get_statusBar(self):
        self.statusBar = QStatusBar()
        self.file_path = QTextEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setFrameShape(False)
        self.file_path.setFixedSize(400, 25)
        self.file_path.setObjectName('open_pushbutton')

        self.edit_mode=0 # 0 null 1anno 2 check
        self.edit_model_label = QLabel("    当前模式:  无  ")
        self.statusBar.addWidget(self.edit_model_label)
        self.key_label = QLabel("key:    ")
        self.statusBar.addPermanentWidget(self.key_label, 0)

        self.position_label = QLabel("point:0,0")
        self.statusBar.addPermanentWidget(self.position_label, 0)

        self.next_page = QPushButton(self)
        self.next_page.setGeometry(20, 10, 100, 30)
        self.next_page.setObjectName('open_pushbutton')
        self.next_page.setText('下一页')
        self.next_page.clicked.connect(self.open_next)

        self.statusBar.addPermanentWidget(self.next_page, 0)
        self.statusBar.addPermanentWidget(QLabel("    "), 0)
        self.label_path = QLabel("路径:")
        self.statusBar.addPermanentWidget(self.label_path, 0)

        self.statusBar.addPermanentWidget(self.file_path, 0)
        self.statusBar.addPermanentWidget(QLabel("    "), 0)
        self.setStatusBar(self.statusBar)

    def select_cls(self):
        source = self.sender()

        self.cls_level = source.objectName().split("_")[0]
        if self.cls_level == "cls1":
            cls_index_1 = int(source.objectName().split("_")[1])
            print(cls_index_1)
            self.cls_index_1 = cls_index_1
            source.setStyleSheet(f"border:2px solid rgb{colors[cls_index_1]};")
        # else:
        #     cls_index_2 = int(source.objectName().split("_")[1])
        #     self.cls_index_2 = cls_index_2
        #     source.setStyleSheet(f"border:2px solid rgb{colors[cls_index_2]};")
        if self.last_cls is not None and self.last_cls[:4] == source.objectName()[:4]:
            last_Button = self.findChild(QPushButton, self.last_cls)
            last_Button.setStyleSheet("")
            # last_Button.setStyleSheet(f"border:1px solid rgb(255, 255, 255);")
        self.last_cls = source.objectName()
        print(self.last_cls)

    ##移动图片到del下
    def delete(self):
        self.key_label.setText("key:Del ")
        self.key_del = True

    def open(self):

        file_path = QFileDialog.getExistingDirectory(self, '选择文文件夹', self.initial_path)
        if file_path == None:
            QMessageBox.information(self, '提示', '文件为空，请重新操作')
        elif len(file_path) == 0:
            pass
        else:
            self.initial_path=file_path
            print(self.initial_path)
            self.edit_mode = 0  # 0 null 1anno 2 check
            self.start_img_viewer()
    
    def changeIndex(self):
        pass


    ##筛选正样本
    def select_positve(self):
        pass
    

    ##筛选负样本
    def select_negative(self):
        if self.edit_mode != 2:
            QMessageBox.warning(self, '错误', '不在检查模式')
            return
        else:
            self.negative_flag = True
            print('negative flage: %s'%(self.negative_flag))



    def start_img_viewer(self):
   
        for i in range(self.page_count):
            willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
            if willselect is None:
                continue
            else:
                willselect.deleteLater()

        if not os.path.isfile('classes.csv'):
            with open('classes.csv', 'w', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                columns = copy.deepcopy(self.cls_1) 
                columns.insert(0,'image')
                csv_writer.writerow(columns)
        
        if self.initial_path is None or len(self.initial_path)==0:
            QMessageBox.warning(self, '错误', '文件为空，请选择文件夹')
            return
    
        if self.edit_mode == 0 or self.edit_mode == 2:  # 0 null 1 mark 2 check
            if self.edit_mode==2:
                self.key_shift = False
                self.key_control = False
                self.key_del = False
                self.negative_flag=False
                self.grid_index_last = -1
                self.page_index =-1
                # for i in range(self.page_count):
                #     willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
                #     if willselect is None:
                #         continue
                #     else:
                #         willselect.deleteLater()
            else:
                self.jimi_config.set("default", "last_dir",self.initial_path)
                self.jimi_config.write(open(self.config_file_path,"w"))
            g = os.walk(self.initial_path)
            self.img_files = ['%s/%s' % (i[0], j) for i in g for j in i[-1] if
                              j.endswith('jpg') or j.endswith('png') or j.endswith('jpeg')]
            self.img_total = len(self.img_files)
            if self.img_total==0:
                QMessageBox.warning(self, '错误', '文件为空，请选择文件夹')
                return
            self.change_mode_pushbutton.setText('点切检查模式')
            self.setWindowTitle(f"当前模式:标注模式 {self.initial_path}")
            self.edit_model_label.setText(f"    当前模式:标注模式 {self.initial_path}")
            self.edit_mode = 1

        
        elif self.edit_mode == 1:
            
            if self.cls_index_1 < 0:
                QMessageBox.warning(self, '错误', '请先选择分类')
                return
           
            self.key_shift = False
            self.key_control = False
            self.key_del = False
            self.negative_flag=False
            self.grid_index_last = -1
            self.page_index = -1
            # start = time.time()
            # for i in range(self.page_count):
            #     willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
            #     if willselect is None:
            #         continue
            #     else:
            #         willselect.deleteLater()
            # print(time.time() - start)
            # self.initial_path=self.get_save_dir()
            # print(os.path.basename(self.initial_path))
            # g = os.walk(self.initial_path)
            # self.img_files = ['%s/%s' % (i[0], j) for i in g for j in i[-1] if
            #                   j.endswith('jpg') or j.endswith('png') or j.endswith('jpeg')]
            
            cls_label = self.get_class()
            df = pd.read_csv('classes.csv')
            df_cls = df[df[cls_label] > 0]
            self.img_files = df_cls['image'].values.tolist()

            self.img_total = len(self.img_files)
            
            if self.img_total == 0:
                QMessageBox.warning(self, '错误', '文件为空，请选择文件夹')
                return
            self.change_mode_pushbutton.setText('点切标注模式')
            self.setWindowTitle(f"当前模式:检查模式 {self.initial_path}")
            self.edit_model_label.setText(f"    当前模式:检查模式 {self.initial_path}")
            self.edit_mode = 2
            
        if self.img_total % self.page_count < self.page_count - 1:
            for i in range(-(self.img_total % self.page_count) + self.page_count):
                self.img_files.append(None)
        tabel_datas=self.img_files[:self.page_count]
        self.page_index=1
        if self.img_total <= self.page_index * self.page_count:
            self.next_page.setEnabled(False)
        else:
            self.next_page.setEnabled(True)
        self.pic_count = len(tabel_datas)

        self.label_path.setText(f"共:{self.img_total}条 当前{self.page_index} 页 共 {self.img_total//self.page_count+1} 页 路径:")
        pic_of_columns = self.get_grid_cols()

        print('pic_count',self.pic_count,'cols',pic_of_columns,'rows',self.pic_count//pic_of_columns+1)
        if self.pic_count !=0:
            for i in range(self.pic_count):
                image_path = tabel_datas[i]
                pixmap = QPixmap(image_path)
                self.addImage(i,pixmap, image_path)

        else:
            QMessageBox.warning(self,'错误','图片个数为0')


    def loc_fil(self,stre):
        print('存放地址为{}'.format(stre))
        self.initial_path = stre

    def addImage(self,item_index, pixmap, image_path):
        #图像法列数
        self.max_columns = self.get_grid_cols()
        self.col = item_index%self.max_columns
        self.row =item_index//self.max_columns
        clickable_image = QClickableImage(self,self.displayed_image_size, self.displayed_image_size, pixmap, image_path)
        clickable_image.setObjectName("item_"+str(item_index))
        clickable_image.clicked.connect(self.on_left_clicked)
        clickable_image.rightClicked.connect(self.on_right_clicked)
        self.gridLayout.addWidget(clickable_image, self.row, self.col)
        QApplication.processEvents()

    def on_left_clicked(self,image_path):
        print(image_path)
        self.file_path.setText(image_path)
   
        
    def on_right_clicked(self,image_path):
        print('right clicked - image id = ' + image_path)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        # def keyPressEvent(self, a0: QtGui.QKeyEvent):
        if event.key()==QtCore.Qt.Key_Delete:
            self.key_label.setText("key:Del ")
            self.key_del = True
        elif event.key() == QtCore.Qt.Key_Shift:
            self.key_label.setText("key:Shift  " )
            self.key_shift = True
        elif event.key() == QtCore.Qt.Key_A and QApplication.keyboardModifiers()==Qt.ControlModifier:
              print("ctrl a")
        elif event.key() == QtCore.Qt.Key_Control:
            self.key_label.setText("key:Control ")
            self.key_control = True

    # def get_save_dir(self):
    #     if self.cls_level == "cls1":
    #         dir_cls = self.cls_1[self.cls_index_1]
    #         # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
    #         return self.save_dir + "/" + dir_cls\
    
    def get_class(self):
        if self.cls_level == "cls1":
            cls_label = self.cls_1[self.cls_index_1]
            # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
            return cls_label

        # else:
        #     dir_cls = ""
        #     if self.mainUI.cls_index_1 >= 0:
        #         dir_cls = self.cls_1[self.cls_index_1] + "/"
        #     dir_cls_2 = self.cls_2[self.cls_index_2]
        #     os.makedirs(self.save_dir + "/" + dir_cls + dir_cls_2, exist_ok=True)
        #     return self.save_dir + "/" + dir_cls + dir_cls_2

    def get_grid_cols(self):
        #展示图片的区域
        scroll_area_images_width = self.width
        if scroll_area_images_width > self.displayed_image_size:
            pic_of_columns = scroll_area_images_width // (self.displayed_image_size+2 ) #计算出一行几列；
        else:
            pic_of_columns = 1
        return pic_of_columns

    def setDisplayedImageSize(self,image_size):
        self.displayed_image_size = image_size

class SaveThread(QThread):
    saveSignal=pyqtSignal(str,list)
    def __init__(self,file_dir,paths):
        super(SaveThread,self).__init__()
        self.file_dir=file_dir
        self.paths=paths
    def run(self):
        for path in self.paths:
            target_file=self.file_dir+ "/"+os.path.basename(path)
            if os.path.exists(path):
                pass
                # shutil.move(path,target_file)
        self.paths.clear()

class QClickableImage(QWidget):
    image_path = None
    out_path = None
    clicked = pyqtSignal(object)
    rightClicked = pyqtSignal(object)
    def __init__(self,mainWindow,width =0,height =0,pixmap =None,image_path = ''):
        QWidget.__init__(self)
        self.mainUI=mainWindow
        self.layout =QVBoxLayout(self)
        self.layout.setContentsMargins(1,1,1,1)
        self.layout.setAlignment(Qt.AlignCenter)
        self.label1 = QLabel()
        self.label1.setObjectName('label1')
        self.setAutoFillBackground(True)
        self.width =width
        self.height = height
        self.pixmap =pixmap
        self.high_light=0
        if self.width and self.height:
            self.resize(self.width,self.height)
        if self.pixmap:
            pixmap = self.pixmap.scaled(QSize(self.width,self.height),Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.label1.setPixmap(pixmap)
            self.image_path = image_path
            # self.label1.setAlignment(Qt.AlignBottom)
            self.layout.addWidget(self.label1)
        self.resize(width,height)


    def enterEvent(self, item):
        pass
        # item.setBackground(QtGui.QColor('moccasin'))

    def leaveEvent(self, item):
        if self.mainUI.key_control or self.mainUI.key_shift or self.mainUI.key_del:
            return
            # saveThread = SaveThread(save_dir, self.mainUI.will_changes)
            # saveThread.start()
            # saveThread.exec()

    def mousePressEvent(self,ev):
        if ev.button() == Qt.RightButton:
            print('RightButton')
            if self.image_path is None:
                return
            # self.setWindowFlags(Qt.FramelessWindowHint)
            self.rightClicked.emit(self.image_path)
        else:
            if self.mainUI.cls_index_1 <0:
                QMessageBox.warning(self, '错误', '请先选择分类')
                return
            if self.image_path is None:
                return
            palettel = QtGui.QPalette()

            if self.mainUI.cls_index_1>=0:
                tmp = colors_2[self.mainUI.cls_index_1]
            else:
                tmp = colors_2[self.mainUI.cls_index_2]
            grid_index_current = self.mainUI.gridLayout.indexOf(self)
            current_position = self.mainUI.gridLayout.getItemPosition(grid_index_current)

            if self.mainUI.grid_index_last>=0:
                last_position = self.mainUI.gridLayout.getItemPosition(self.mainUI.grid_index_last)

            if self.mainUI.key_shift and self.mainUI.grid_index_last>-1:
                last_index=last_position[0]*self.mainUI.get_grid_cols()+ last_position[1]
                now_index=current_position[0]*self.mainUI.get_grid_cols()+ current_position[1]
                last_widget = self.mainUI.gridLayout.itemAtPosition(last_position[0], last_position[1]).widget()

                start=min(now_index,last_index)
                end=max(now_index,last_index)
                for i in range(start, end+1):
                    willselect = self.mainUI.scroll_ares_images.findChild(QClickableImage, "item_"+str(i))
                    if willselect is None:
                        continue
                    if last_widget.high_light==1:
                        if willselect not in self.mainUI.will_changes:
                            # save_dir = self.mainUI.get_save_dir()
                            # willselect.out_path = save_dir + "/" + os.path.basename(willselect.image_path)
                            self.mainUI.will_changes.append(willselect)
                            palettel.setColor(willselect.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                            willselect.setPalette(palettel)
                            willselect.high_light = 1
                        # willselect.image_path=willselect.out_path
                    elif willselect  in self.mainUI.will_changes:
                        palettel = QtGui.QPalette()
                        palettel.setColor(willselect.backgroundRole(), QColor(255, 255, 255))
                        # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                        willselect.setPalette(palettel)
                        willselect.high_light = 0
                        if willselect in self.mainUI.will_changes:
                            self.mainUI.will_changes.remove(willselect)
                self.mainUI.key_shift=False
                self.mainUI.key_label.setText("key:none   ")

            elif self.mainUI.key_control and self.mainUI.grid_index_last > -1:

                last_widget=self.mainUI.gridLayout.itemAtPosition(last_position[0],last_position[1]).widget()
                start = (min(current_position[0], last_position[0]),min(current_position[1], last_position[1]))
                end = (max(current_position[0], last_position[0]),max(current_position[1], last_position[1]))

                for i in range(start[0], end[0]+1):
                    for j in range(start[1], end[1]+1):

                        tmp_index=i*self.mainUI.get_grid_cols()+j
                        willselect = self.mainUI.scroll_ares_images.findChild(QClickableImage, "item_" + str(tmp_index))
                        if willselect is None:
                            print("none", "item_" + str(i))
                            continue
                        if last_widget.high_light==1:
                            if willselect not in self.mainUI.will_changes:
                                # save_dir = self.mainUI.get_save_dir()
                                self.mainUI.will_changes.append(willselect)
                                palettel.setColor(willselect.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                                willselect.setPalette(palettel)
                                willselect.high_light = 1
                        elif  willselect in self.mainUI.will_changes:
                            palettel = QtGui.QPalette()
                            palettel.setColor(willselect.backgroundRole(), QColor(255, 255, 255))
                            # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                            willselect.setPalette(palettel)
                            willselect.high_light = 0
                            if willselect in self.mainUI.will_changes:
                                self.mainUI.will_changes.remove(willselect)
                self.mainUI.key_control = False
                self.mainUI.key_label.setText("key:none   ")

            elif self.mainUI.key_del and self.mainUI.grid_index_last > -1:
                self.mainUI.key_del = False
                self.mainUI.key_label.setText("key:none   ")

            else:
                if self.high_light == 0:
                    # save_dir = self.mainUI.get_save_dir()

                    self.mainUI.will_changes.append(self)
                    palettel = QtGui.QPalette()
                    palettel.setColor(self.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                    # palettel.setColor(self.backgroundRole(),QColor(255,0,0))
                    self.setPalette(palettel)
                    self.high_light = 1
                else:
                    palettel = QtGui.QPalette()
                    palettel.setColor(self.backgroundRole(), QColor(255, 255, 255))
                    # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                    self.setPalette(palettel)
                    self.high_light = 0
                    if self in self.mainUI.will_changes:
                        self.mainUI.will_changes.remove(self)
            self.mainUI.grid_index_last = grid_index_current
            self.mainUI.position_label.setText(
                f"point:{current_position[0]},{current_position[1]},{len(self.mainUI.will_changes)}")
            # self.setStyleSheet("background-color: rgb(255,0,0); margin:5px; border:1px solid rgb(0, 255, 0); ")
            self.clicked.emit(self.image_path)

    def imageId(self):
        return self.image_path



if __name__ =='__main__':
    app =QApplication(sys.argv)
    windo = Img_viewed()
    windo.showMaximized()
    sys.exit(app.exec_())