import configparser
import shutil

from PIL import ImageDraw, Image, ImageQt, ImageFont
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import sys
import time
import json
import csv
from numpy.lib.utils import source
import pandas as pd
import copy

colors = ['(0,255,0)', '(255,0,0)', '(0,0,255)', '(255,255,0)', '(255,0,255)', '(0,255,255)', '(22,7,201)']
colors_2 = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (22, 7, 201),
            (30, 144, 255), (0, 139, 0), (192, 255, 62)
    , (255, 255, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (22, 7, 201), (30, 144, 255), (0, 139, 0),
            (192, 255, 62)]

class McrollArea(QScrollArea):
    def __init__(self, parent):
        QScrollArea.__init__(self, parent)
        self.mainUI = parent

    def wheelEvent(self, event):
        if (not self.mainUI.key_shift) and (not self.mainUI.key_control) and len(self.mainUI.will_changes) > 0:
            # self.mainUI.df = pd.read_csv(self.mainUI.test_file)     ##new line
            for will_weight in self.mainUI.will_changes:
                
                if os.path.exists(will_weight.image_path):
                    related_path=will_weight.image_path.replace(self.mainUI.initial_path,"")
                    related_path = related_path.replace('\\','/')
                if not (self.mainUI.df_test.img_path == related_path).any():
                    i = len(self.mainUI.df_test) + 1
                    self.mainUI.df_test.loc[i] = [related_path, 0, 0, 0, 0, 0, 0]
                if self.mainUI.normal_flag:
                    for cls in self.mainUI.cls_1:
                        self.mainUI.df_test.loc[(self.mainUI.df_test.img_path == related_path), cls] = 0
                    will_weight.deleteLater()
                else:
                    for cls in self.mainUI.class_name_set:
                        if (self.mainUI.df_test.loc[(self.mainUI.df_test.img_path == related_path), cls]).any() == 0:
                            self.mainUI.df_test.loc[(self.mainUI.df_test.img_path == related_path), cls] = 1
                        else:
                            self.mainUI.df_test.loc[(self.mainUI.df_test.img_path == related_path), cls] = 0
                        
                        # self.mainUI.df_test.loc[(self.mainUI.df_test.img_path == related_path), self.mainUI.combox_name] = self.mainUI.cls_item_index
                    # self.mainUI.df_test.drop_duplicates(subset=['img_path'], keep='first', inplace=True)
                    # will_weight.image_path=will_weight.out_path
                    will_weight.deleteLater()
            self.mainUI.normal_flag = False
            self.mainUI.btn_select_set.clear()
            self.mainUI.class_name_set.clear()
            self.mainUI.will_changes.clear()
            for i in range(len(self.mainUI.cls_1)):
                btn = self.mainUI.findChild(QPushButton, self.mainUI.cls_1[i])
                btn.setStyleSheet('')
            self.mainUI.df_test.to_csv(self.mainUI.test_file, index=False)
        else:
            super().wheelEvent(event)
        if self.mainUI.gridLayout.count() == 0 and self.mainUI.next_page.isEnabled():
            if self.mainUI.next_page.isEnabled():
                self.mainUI.page_index += 1
                self.mainUI.last_page.setEnabled(True)
                self.mainUI.open_next()

        # if self.verticalScrollBar().value()%self.parent().height>0:
        #     print("next",self.verticalScrollBar().value()%self.parent().height)
        # print('wheelEvent',self.verticalScrollBar().value(),self.parent().pic_count,self.parent().get_grid_cols(),self.parent().pic_count//self.parent().get_grid_cols())


class Img_viewed(QMainWindow):
    _signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(Img_viewed, self).__init__(parent)
        self.parent = parent
        self.width = 1920
        self.height = 1080 - 70
        self.setWindowTitle('cls label')
        self.resize(self.width, self.height)
        ## read config file
        self.jimi_config = configparser.ConfigParser()
        self.config_file_path = 'label_config.ini'
        self.jimi_config.read(self.config_file_path)
        self.cls_1 = self.jimi_config.get("cls", "1").split(",")  ## return list of classes
        self.initial_path = self.jimi_config.get("default", "last_dir")
        self.initial_path=self.initial_path[:-1]+self.initial_path[-1].replace("/","").replace("\\","")
        self.test_file =os.path.join(self.initial_path,self.jimi_config.get("cls", "test_file"))
        self.train_file =os.path.join(self.initial_path, self.jimi_config.get("cls", "train_file"))

        if not os.path.isfile(self.test_file):
            with open(self.test_file, 'w', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                columns = copy.deepcopy(self.cls_1)
                columns.insert(0, 'img_path')
                csv_writer.writerow(columns)
        self.df_test = pd.read_csv(self.test_file)
        self.pic_width = self.jimi_config.getint("default", "pic_width")
        if len(self.cls_1) == 0:
            QMessageBox.warning(self, '错误', 'label_config cls 1不能为空')
            exit(1)

        self.cls_items = []
        for cls_positionin in self.cls_1:
            temp = cls_positionin.split('/')
            temp.insert(0, "normal")
            self.cls_items.append(temp)
        self.scroll_ares_images = McrollArea(self)
        self.scroll_ares_images.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget(self)
        self.scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContends')

        self.init_data()

        # 进行网络布局
        # self.scroll_ares_images.wheelEvent()
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setSpacing(1)
        self.gridLayout.setContentsMargins(1, 1, 1, 1)
        self.scroll_ares_images.setWidget(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.gridLayout)
        self.scroll_ares_images.setGeometry(10, 50, self.width - 120, self.height - 80)
        self.get_statusBar()
    
        self.normal_btn = QPushButton(self)
        self.normal_btn.setGeometry(1820, 120, 70, 50)
        self.normal_btn.setObjectName('normal')
        self.normal_btn.setText('normal')
        self.normal_btn.is_select=False
        self.normal_btn.clicked.connect(self.be_normal)

        for i in range(len(self.cls_1)):
            self.current_cls1 = QPushButton(self)
            self.current_cls1.setGeometry(1820, 200+i*80, 70, 50)
            self.current_cls1.setObjectName(self.cls_1[i])
            self.current_cls1.setText(self.cls_1[i])
            self.current_cls1.is_select=False
            self.current_cls1.select_index=i
            self.current_cls1.clicked.connect(self.single_select)

        
        self.open_file_pushbutton = QPushButton(self)
        self.open_file_pushbutton.setGeometry(20, 10, 100, 30)
        self.open_file_pushbutton.setObjectName('open_pushbutton')
        self.open_file_pushbutton.setText('打开文件夹')
        self.open_file_pushbutton.clicked.connect(self.open)

        self.label_cls1 = QLabel(self)
        self.label_cls1.setText("选择主分类:")
        self.label_cls1.setGeometry(150 + 150, 10, 80, 30)

        self.cb = QComboBox(self)
        self.cb.setGeometry(150 + 150 + 70, 10, 160, 30)
        self.cb.setObjectName('combo')
        for item in (self.cls_1):
            self.cb.addItem(item)
        self.cb.setCurrentIndex(0)

        for i in range(max(self.cls_count)):
            self.cls_select_btn = QPushButton(self)
            self.cls_select_btn.setGeometry(150 + 80 + (len(self.cls_1) + i) *90, 10, 80, 30)
            self.cls_select_btn.setObjectName('cls1_' + str(i))
            self.cls_select_btn.setText('cls1_' + str(i))
            self.cls_select_btn.clicked.connect(self.select_cls)
            self.cls_select_btn.hide()
        self.changecls(0, self.cls_1[0])
        self.cb.currentIndexChanged.connect(self.changeIndex)  # 发射currentIndexChanged信号，连接下面的selectionchange槽
       

        self.change_mode_pushbutton = QPushButton(self)
        self.change_mode_pushbutton.setGeometry(150, 10, 130, 30)
        self.change_mode_pushbutton.setObjectName('start')
        self.change_mode_pushbutton.setText('检查标注')
        self.change_mode_pushbutton.clicked.connect(self.start_check_model)

        self.to_train_btn = QPushButton(self)
        self.to_train_btn.setGeometry(1400, 10, 120, 30)
        self.to_train_btn.setObjectName('start')
        self.to_train_btn.setText('转训练')
        self.to_train_btn.clicked.connect(self.to_train_event)
        self.slit_train_btn = QPushButton(self)
        self.slit_train_btn.setGeometry(1540, 10, 120, 30)
        self.slit_train_btn.setObjectName('start')
        self.slit_train_btn.setText('分配训练')
        self.slit_train_btn.clicked.connect(self.split_train_test)

        self.del_file_pushbutton = QPushButton(self)
        self.del_file_pushbutton.setGeometry(600, 10, 80, 30)
        self.del_file_pushbutton.setObjectName('del')
        self.del_file_pushbutton.setText('delete')
        self.del_file_pushbutton.clicked.connect(self.deleteEvent)
        # self.positive_pushbutton = QPushButton(self)
        # self.positive_pushbutton.setGeometry(150 + 150 +80+ (len(self.cls_1)) * 100, 10, 50, 30)
        # self.positive_pushbutton.setObjectName('positive')
        # self.positive_pushbutton.setText('正样本')
        # self.positive_pushbutton.clicked.connect(self.select_positve)

        self.last_Button=None

        self.vertocal = QVBoxLayout()
        self.vertocal.addWidget(self.scroll_ares_images)
        self.show()
        # 设置图片的预览尺寸；
        self.displayed_image_size = self.pic_width
        self.page_count = 18 * 9 * 3
        self.img_total=0
        self.col = 0
        self.row = 0
        self.m_drag = False
        # self.init_data()

    def init_data(self):

        self.last_cls = None
        self.cls_index_1 = -1
        self.cls_index_2 = -1
        self.cls_level = None

        self.key_shift = False
        self.key_control = False
        self.normal_flag = False

        self.cls_item_name = None
        self.cls_item_index = -1
        self.cls_count = []

        self.grid_index_last = -1
        self.page_index = -1
        self.will_changes = []

        self.class_name_set = set()
        self.btn_select_set = set()
        self.btn_color_set = set()
        self.edit_mode_current_button = []
        # white = []
        for item in self.cls_1:
            cls_list = item.split('/')
            length = len(cls_list)+1
            self.cls_count.append(length)
        # self.create_button_index = copy.deepcopy(white)

    def open_last(self):
        self.page_index -= 1
        if self.page_index<=1:
            self.last_page.setEnabled(False)
        self.open_next()

    def next_btn(self):
        self.page_index += 1
        self.last_page.setEnabled(True)
        self.open_next()

    def open_next(self):
        self.key_shift = False
        self.key_control = False

        self.grid_index_last = -1
        self.will_changes = []


        if self.img_total:
            for i in range(self.page_count):
                willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
                if willselect is None:
                    continue
                else:
                    willselect.deleteLater()
        self.will_changes.clear()
        self.scroll_ares_images.verticalScrollBar().setValue(0)
        if self.img_total <= self.page_index * self.page_count:
            self.next_page.setEnabled(False)
        else:
            self.next_page.setEnabled(True)

        tabel_datas = self.img_files[self.page_count * (self.page_index - 1):self.page_count * self.page_index]

        self.pic_count = len(tabel_datas)

        self.label_path.setText(
            f"共:{self.img_total}条 当前{self.page_index} 页 共 {self.img_total // self.page_count + 1} 页 路径:")
        if self.img_total // self.page_count > 0:
            self.label_path.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")
        else:
            self.label_path.setStyleSheet("")
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

        self.edit_mode = 0  # 0 null 1anno 2 check
        self.edit_model_label = QLabel("    当前模式:  无  ")
        self.statusBar.addWidget(self.edit_model_label)
        self.key_label = QLabel("key:    ")
        self.statusBar.addPermanentWidget(self.key_label, 0)

        self.position_label = QLabel("point:0,0")
        self.statusBar.addPermanentWidget(self.position_label, 0)

        self.last_page = QPushButton(self)
        self.last_page.setGeometry(20, 10, 100, 30)
        self.last_page.setObjectName('open_pushbutton')
        self.last_page.setText('上一页')
        self.last_page.clicked.connect(self.open_last)
        self.last_page.setEnabled(False)

        self.next_page = QPushButton(self)
        self.next_page.setGeometry(20, 10, 100, 30)
        self.next_page.setObjectName('open_pushbutton')
        self.next_page.setText('下一页')
        self.next_page.clicked.connect(self.next_btn)

        self.statusBar.addPermanentWidget(self.last_page, 0)
        self.statusBar.addPermanentWidget(self.next_page, 0)
        self.statusBar.addPermanentWidget(QLabel("    "), 0)
        self.label_path = QLabel("路径:")
        self.statusBar.addPermanentWidget(self.label_path, 0)

        self.statusBar.addPermanentWidget(self.file_path, 0)
        self.statusBar.addPermanentWidget(QLabel("    "), 0)
        self.setStatusBar(self.statusBar)

    def changecls(self, index, name):
        for i in range(max(self.cls_count)):
            willselect = self.findChild(QPushButton, 'cls1_' + str(i))
            if willselect:
                willselect.hide()
        self.combox_index = index
        self.combox_name = name
        temp = self.cls_1[index].split('/')
        temp.insert(0, "normal")

        for i in range(self.cls_count[index]):
            if i==self.cls_item_index:
                self.cls_item_name=self.cls_items[index][i]
            willselect = self.findChild(QPushButton, 'cls1_' + str(i))
            willselect.setText(self.cls_items[index][i])
            willselect.show()

    def changeIndex(self):
        source = self.sender()
        index = source.currentIndex()
        name = source.itemText(index)
        source.setStyleSheet(f"border:2px solid rgb{colors[index]};")
        self.changecls(index, name)

    def select_cls(self):
        source = self.sender()
        self.cls_item_index = int(source.objectName().split("_")[1])
        self.cls_item_name = source.text()
        source.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")

        if self.last_Button:
            self.last_Button.setStyleSheet("")
        self.last_Button = source
    
    def be_normal(self):
            self.normal_flag = True
            for col in self.df_test.columns[1:]:
                btn = self.findChild(QPushButton, col)
                btn.setStyleSheet("")
            self.btn_color_set.clear()
            self.btn_select_set.clear()
            self.class_name_set.clear()
    


    def single_select(self):
        source = self.sender()
        if source not in self.btn_select_set:
            self.btn_select_set.add(source)
            source.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")
            self.class_name_set.add(source.text())
        else:
            source.setStyleSheet("")
            self.class_name_set.remove(source.text())
            self.btn_select_set.remove(source)
        
        if self.edit_mode == 1:
            if source not in self.btn_color_set:
                self.btn_color_set.add(source)
                source.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")
            else:
                source.setStyleSheet("")
                self.btn_color_set.remove(source)


    def open(self):

        file_path = QFileDialog.getExistingDirectory(self, '选择文文件夹', self.initial_path)
        if file_path == None:
            QMessageBox.information(self, '提示', '文件为空，请重新操作')
        elif len(file_path) == 0:
            pass
        else:
            self.initial_path = file_path
            print(self.initial_path)

            self.test_file =os.path.join(self.initial_path , self.jimi_config.get("cls", "test_file"))
            self.train_file =os.path.join(self.initial_path, self.jimi_config.get("cls", "train_file"))
            self.edit_mode = 0  # 0 null 1anno 2 check
            self.setWindowTitle(f"当前模式:标注模式 {self.initial_path}")
            self.edit_model_label.setText(f"    当前模式:标注模式 {self.initial_path}")
            self.start_img_viewer()

    def start_check_model(self):

        if self.cls_item_index < 0:
            QMessageBox.warning(self, '错误', '请先选择分类')
            return

        self.edit_mode = 1
        self.change_mode_pushbutton.setText('检查标注:'+self.cls_item_name)
        self.setWindowTitle(f"当前模式:检查模式 {self.cls_item_name} {self.initial_path}")
        self.edit_model_label.setText(f"    当前模式:检查模式 {self.initial_path}")
        self.start_img_viewer()

    def to_train_event(self):
        if len(self.will_changes) > 0:
            if not os.path.exists(self.train_file):
                with open(self.train_file, 'w', encoding='utf-8') as f:
                    csv_writer = csv.writer(f)
                    columns = copy.deepcopy(self.cls_1)
                    columns.insert(0, 'img_path')
                    csv_writer.writerow(columns)
            df_train = pd.read_csv(self.train_file)
            for will_weight in self.will_changes:
                if os.path.exists(will_weight.image_path):
                    related_path = will_weight.image_path.replace(self.initial_path, "")
                    if not (df_train.img_path == related_path).any():
                        i = len(df_train) + 1
                        df_train.loc[i] =self.df_test[self.df_test.img_path == related_path].values[0].tolist()
                    # df_train.loc[(df_train.img_path == related_path)] = self.df_test[self.df_test.img_path == related_path].values[0].tolist()
                    self.df_test.drop(self.df_test[self.df_test.img_path == related_path].index, inplace=True)
                    will_weight.deleteLater()
            self.will_changes.clear()
            df_train.to_csv(self.train_file, index=False)
            self.df_test.to_csv(self.test_file, mode='w', index=False)

    def split_train_test(self):

        if not os.path.exists(self.test_file):
            QMessageBox.warning(self, '错误',self.test_file+"未找到")
            return

        shuffle_data = self.df_test.sample(frac=1).reset_index(drop=True)

        datas = shuffle_data.values.tolist()

        # train_data= datas[:len(shuffle_data) // 2]

        test_data = datas[len(shuffle_data) // 2:]

        if not os.path.exists(self.train_file):
            with open(self.train_file, 'w', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                columns = copy.deepcopy(self.cls_1)
                columns.insert(0, 'img_path')
                csv_writer.writerow(columns)
        df_train = pd.read_csv(self.train_file)

        for index, data in  enumerate(test_data):
            df_train.loc[index+1]=data
            self.df_test.drop(self.df_test.index[(self.df_test["img_path"] == data[0])].values, inplace=True)
        df_train.to_csv(self.train_file,index=False)
        self.df_test.to_csv(self.test_file, mode='w', index=False)

        self.slit_train_btn.setText('分配训练:ok')


    def start_img_viewer(self):
        if self.initial_path is None or len(self.initial_path) == 0:
            QMessageBox.warning(self, '错误', '文件为空，请选择文件夹')
            return

        if self.img_total:
            for i in range(self.page_count):
                willselect = self.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
                if willselect is None:
                    continue
                else:
                    willselect.deleteLater()
        self.key_shift = False
        self.key_control = False
        self.grid_index_last = -1
        self.page_index = -1
        self.will_changes.clear()
        self.scroll_ares_images.verticalScrollBar().setValue(0)
        if self.edit_mode == 0:  # 0 null 1 mark 2 check

            self.jimi_config.set("default", "last_dir", self.initial_path)
            self.jimi_config.write(open(self.config_file_path, "w"))
            g = os.walk(self.initial_path)
            self.img_files = ['%s/%s' % (i[0], j) for i in g for j in i[-1] if
                              j.endswith('jpg') or j.endswith('png') or j.endswith('jpeg')]
            self.img_total = len(self.img_files)
            if self.img_total == 0:
                QMessageBox.warning(self, '错误', '文件为空，请选择文件夹')
                return

        elif self.edit_mode == 1:
            df_cls = self.df_test[self.df_test[self.combox_name] == int(self.cls_item_index)]
            self.img_files = df_cls['img_path'].values.tolist()
            self.img_total = len(self.img_files)
            if self.img_total<1:
                self.change_mode_pushbutton.setText('检查标注:无数据')
                return
            conn_str="/"
            if self.img_files[0].startswith("/"):
                conn_str = ""
            for i in range(self.img_total):
                self.img_files[i]=self.initial_path+conn_str+self.img_files[i]

        if self.img_total % self.page_count < self.page_count - 1:
            for i in range(-(self.img_total % self.page_count) + self.page_count):
                self.img_files.append(None)
        tabel_datas = self.img_files[:self.page_count]
        self.page_index = 1
        if self.img_total <= self.page_index * self.page_count:
            self.next_page.setEnabled(False)
        else:
            self.next_page.setEnabled(True)
        self.last_page.setEnabled(False)
        self.pic_count = len(tabel_datas)

        self.label_path.setText(
            f"共:{self.img_total}条 当前{self.page_index} 页 共 {self.img_total // self.page_count + 1} 页 路径:")

        if self.img_total // self.page_count>0:
            self.label_path.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")
        else:
            self.label_path.setStyleSheet("")
        pic_of_columns = self.get_grid_cols()

        if self.pic_count != 0:
            for i in range(self.pic_count):
                image_path = tabel_datas[i]
                if image_path is not None:
                    if not os.path.exists(image_path):
                        related_path = image_path.replace(self.initial_path, "")
                        # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
                        self.df_test.drop(self.df_test[self.df_test.img_path == related_path].index, inplace=True)
                pixmap = QPixmap(image_path)
                self.addImage(i, pixmap, image_path)
            self.df_test.to_csv(self.test_file, index=False)
        else:
            QMessageBox.warning(self, '错误', '图片个数为0')

    def loc_fil(self, stre):
        print('存放地址为{}'.format(stre))
        self.initial_path = stre

    def addImage(self, item_index, pixmap, image_path):
        # 图像法列数
        self.max_columns = self.get_grid_cols()
        self.col = item_index % self.max_columns
        self.row = item_index // self.max_columns
        clickable_image = QClickableImage(self, self.displayed_image_size, self.displayed_image_size, pixmap,
                                          image_path)
        clickable_image.setObjectName("item_" + str(item_index))
        clickable_image.clicked.connect(self.on_left_clicked)
        clickable_image.rightClicked.connect(self.on_right_clicked)
        self.gridLayout.addWidget(clickable_image, self.row, self.col)
        QApplication.processEvents()

    def on_left_clicked(self, image_path):
        self.btn_color_set.clear()
        self.file_path.setText(image_path)
        related_path = image_path.replace(self.initial_path,"")
        related_path = related_path.replace('\\','/')
        if self.edit_mode == 1: 
            for col in self.df_test.columns[1:]:
                btn = self.findChild(QPushButton, col)
                btn.setStyleSheet("")
                if (self.df_test.loc[(self.df_test.img_path == related_path), col]).any() == 1:
                    btn = self.findChild(QPushButton, col)
                    # self.btn_select_set.add(btn)
                    self.btn_color_set.add(btn)
                    btn.setStyleSheet(f"border:2px solid rgb{(255, 0, 0)};")
        

    def on_right_clicked(self, image_path):
        print('right clicked - image id = ' + image_path)

    def deleteEvent(self):
        self.del_current()

    def del_current(self):
        if len(self.will_changes) > 0:
            os.makedirs('del', exist_ok=True)
            for will_weight in self.will_changes:
                if os.path.exists(will_weight.image_path):
                    related_path = will_weight.image_path.replace(self.initial_path, "")
                    # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
                    will_weight.out_path = "del/" + os.path.basename(will_weight.image_path)
                    shutil.move(will_weight.image_path, will_weight.out_path)
                    self.df_test.drop(self.df_test[self.df_test.img_path == related_path].index, inplace=True)
                    will_weight.deleteLater()
            self.key_label.setText("key:none   ")
            self.will_changes.clear()
            self.df_test.to_csv(self.test_file, index=False)
            
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        # def keyPressEvent(self, a0: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Delete:
            self.del_current()
        elif event.key() == QtCore.Qt.Key_Shift:
            self.key_label.setText("key:Shift  ")
            self.key_shift = True
        elif event.key() == QtCore.Qt.Key_A and QApplication.keyboardModifiers() == Qt.ControlModifier:
            print("ctrl a")
        elif event.key() == QtCore.Qt.Key_Control:
            self.key_label.setText("key:Control ")
            self.key_control = True

    def get_class(self):
        if self.cls_level == "cls1":
            cls_label = self.cls_1[self.cls_index_1]
            # os.makedirs(self.save_dir + "/" + dir_cls, exist_ok=True)
            return cls_label


    def get_grid_cols(self):
        # 展示图片的区域
        scroll_area_images_width = self.width - 120
        if scroll_area_images_width > self.displayed_image_size:
            pic_of_columns = scroll_area_images_width // (self.displayed_image_size + 2)  # 计算出一行几列；
        else:
            pic_of_columns = 1
        return pic_of_columns

    def setDisplayedImageSize(self, image_size):
        self.displayed_image_size = image_size


class SaveThread(QThread):
    saveSignal = pyqtSignal(str, list)

    def __init__(self, file_dir, paths):
        super(SaveThread, self).__init__()
        self.file_dir = file_dir
        self.paths = paths

    def run(self):
        for path in self.paths:
            target_file = self.file_dir + "/" + os.path.basename(path)
            if os.path.exists(path):
                pass
                # shutil.move(path,target_file)
        self.paths.clear()

font_l = ImageFont.truetype("C:/Windows/Fonts/STFANGSO.TTF", 36)
font = ImageFont.truetype("C:/Windows/Fonts/STFANGSO.TTF", 24)
font_s = ImageFont.truetype("C:/Windows/Fonts/STFANGSO.TTF", 14)

class QClickableImage(QWidget):
    image_path = None
    out_path = None
    clicked = pyqtSignal(object)
    rightClicked = pyqtSignal(object)

    def __init__(self, mainWindow, width=0, height=0, pixmap=None, image_path=''):
        QWidget.__init__(self)
        self.mainUI = mainWindow
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setAlignment(Qt.AlignCenter)
        self.label1 = QLabel()
        self.label1.setObjectName('label1')
        self.setAutoFillBackground(True)
        self.width = width
        self.height = height
        self.pixmap = pixmap
        self.high_light = 0
        if self.width and self.height:
            self.resize(self.width, self.height)
        if self.pixmap:

            if image_path:
                pixmap = self.pixmap.scaled(QSize(self.width, self.height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label1.setPixmap(pixmap)

                # pil_img=Image.open(image_path)
                #
                # image_with_text=self.add_text_to_image(pil_img,"☆☆☆☆☆")
                # pix_mapaa=ImageQt.toqpixmap(image_with_text)
                #
                # # pixmap = self.pixmap.scaled(QSize(self.width, self.height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # pixmap = pix_mapaa.scaled(QSize(self.width, self.height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # self.label1.setPixmap(pixmap)

                self.image_path = image_path
            # self.label1.setAlignment(Qt.AlignBottom)
            self.layout.addWidget(self.label1)
        self.resize(width, height)

    def add_text_to_image(self, image, text, font=font):
        rgba_image = image.convert('RGBA')
        text_overlay = Image.new('RGBA', rgba_image.size, (255, 255, 255, 0))
        # 创建一个可以在给定图像上绘图的对象
        image_draw = ImageDraw.Draw(text_overlay)
        # 返回给定字符串的大小，以像素为单位。 draw.textsize(string,options)⇒ (width, height)
        # 变量option的font用于指定所用字体。它应该是类ImangFont的一个实例，使用ImageFont模块的load()方法从文件中加载的

        if rgba_image.size[0] * rgba_image.size[1] < 90 * 91:
            font = font_s
        if rgba_image.size[0] * rgba_image.size[1] > 64 * 64 * 6:
            font = font_l
        text_size_x, text_size_y = image_draw.textsize(text, font=font)

        text_xy = (rgba_image.size[0] // 2 - text_size_x // 2, rgba_image.size[1] - text_size_y * 5 // 4)
        # 在给定的位置绘制一个字符创。draw.text(position,string, options)
        # 变量position给出了文本的左上角的位置。
        # 变量option的font用于指定所用字体
        # 变量options的fill给定文本的颜色。
        image_draw.text(text_xy, text, font=font, fill=(76, 234, 124, 180))
        # Image.alpha_composite(im1,im2) 将im2复合到im1上，返回一个Image对象
        # im1和im2的size要相同。且im1和im2的mode都必须是RGBA
        image_with_text = Image.alpha_composite(rgba_image, text_overlay)

        return image_with_text
    def enterEvent(self, item):
        pass
        # item.setBackground(QtGui.QColor('moccasin'))

    def leaveEvent(self, item):
        if self.mainUI.key_control or self.mainUI.key_shift:
            return
            # saveThread = SaveThread(save_dir, self.mainUI.will_changes)
            # saveThread.start()
            # saveThread.exec()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.RightButton:
            print('RightButton')
            if self.image_path is None:
                return
            # self.setWindowFlags(Qt.FramelessWindowHint)
            self.rightClicked.emit(self.image_path)
        else:
            # if self.mainUI.cls_index_1 <0:
            #     QMessageBox.warning(self, '错误', '请先选择分类')
            #     return
            if self.image_path is None:
                return
            palettel = QtGui.QPalette()

            if self.mainUI.cls_index_1 >= 0:
                tmp = colors_2[self.mainUI.cls_index_1]
            else:
                tmp = colors_2[self.mainUI.cls_index_2]
            grid_index_current = self.mainUI.gridLayout.indexOf(self)
            current_position = self.mainUI.gridLayout.getItemPosition(grid_index_current)

            if self.mainUI.grid_index_last >= 0:
                last_position = self.mainUI.gridLayout.getItemPosition(self.mainUI.grid_index_last)

            if self.mainUI.key_shift and self.mainUI.grid_index_last > -1:
                last_index = last_position[0] * self.mainUI.get_grid_cols() + last_position[1]
                now_index = current_position[0] * self.mainUI.get_grid_cols() + current_position[1]
                last_widget = self.mainUI.gridLayout.itemAtPosition(last_position[0], last_position[1]).widget()

                start = min(now_index, last_index)
                end = max(now_index, last_index)
                if self.mainUI.edit_mode == 1:
                    for i in range(start, end + 1):
                        willselect = self.mainUI.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
                        if willselect is None:
                            continue
                        if last_widget.high_light == 1:
                            palettel.setColor(self.mainUI.will_changes[-1].backgroundRole(), QColor(255,0,0))
                            self.mainUI.will_changes[-1].setPalette(palettel)
                            if willselect not in self.mainUI.will_changes:
                                self.mainUI.will_changes.append(willselect)
                                # palettel.setColor(willselect.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                                palettel.setColor(willselect.backgroundRole(), QColor(255,0,0))
                                willselect.setPalette(palettel)
                                willselect.high_light = 1
                        elif willselect in self.mainUI.will_changes:
                            palettel = QtGui.QPalette()
                            palettel.setColor(willselect.backgroundRole(), QColor(255, 255, 255))
                            # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                            willselect.setPalette(palettel)
                            willselect.high_light = 0
                            if willselect in self.mainUI.will_changes:
                                self.mainUI.will_changes.remove(willselect)
                    self.mainUI.key_shift = False
                    self.mainUI.key_label.setText("key:none   ")     

                else:
                    for i in range(start, end + 1):
                        willselect = self.mainUI.scroll_ares_images.findChild(QClickableImage, "item_" + str(i))
                        if willselect is None:
                            continue
                        if last_widget.high_light == 1:
                            if willselect not in self.mainUI.will_changes:
                                self.mainUI.will_changes.append(willselect)
                                palettel.setColor(willselect.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                                # palettel.setColor(willselect.backgroundRole(), QColor(255,0,0))
                                willselect.setPalette(palettel)
                                willselect.high_light = 1
                        elif willselect in self.mainUI.will_changes:
                            palettel = QtGui.QPalette()
                            palettel.setColor(willselect.backgroundRole(), QColor(255, 255, 255))
                            # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                            willselect.setPalette(palettel)
                            willselect.high_light = 0
                            if willselect in self.mainUI.will_changes:
                                self.mainUI.will_changes.remove(willselect)
                    self.mainUI.key_shift = False
                    self.mainUI.key_label.setText("key:none   ")

            elif self.mainUI.key_control and self.mainUI.grid_index_last > -1:

                last_widget = self.mainUI.gridLayout.itemAtPosition(last_position[0], last_position[1]).widget()
                start = (min(current_position[0], last_position[0]), min(current_position[1], last_position[1]))
                end = (max(current_position[0], last_position[0]), max(current_position[1], last_position[1]))

                for i in range(start[0], end[0] + 1):
                    for j in range(start[1], end[1] + 1):

                        tmp_index = i * self.mainUI.get_grid_cols() + j
                        willselect = self.mainUI.scroll_ares_images.findChild(QClickableImage, "item_" + str(tmp_index))
                        if willselect is None:
                            print("none", "item_" + str(i))
                            continue
                        if last_widget.high_light == 1:
                            if willselect not in self.mainUI.will_changes:
                                # save_dir = self.mainUI.get_save_dir()
                                self.mainUI.will_changes.append(willselect)
                                palettel.setColor(willselect.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                                willselect.setPalette(palettel)
                                willselect.high_light = 1
                        elif willselect in self.mainUI.will_changes:
                            palettel = QtGui.QPalette()
                            palettel.setColor(willselect.backgroundRole(), QColor(255, 255, 255))
                            # palettel.setColor(self.backgroundRole(), QColor(colors_2[Img_viewed(self.aaa).cls_index_1]))
                            willselect.setPalette(palettel)
                            willselect.high_light = 0
                            if willselect in self.mainUI.will_changes:
                                self.mainUI.will_changes.remove(willselect)
                self.mainUI.key_control = False
                self.mainUI.key_label.setText("key:none   ")

            else:
                if self.high_light == 0:
                    # save_dir = self.mainUI.get_save_dir()
                    self.mainUI.will_changes.append(self)
                    palettel = QtGui.QPalette()
                    palettel.setColor(self.backgroundRole(), QColor(tmp[0], tmp[1], tmp[2]))
                    self.setPalette(palettel)
                    self.high_light = 1
                else:
                    palettel = QtGui.QPalette()
                    palettel.setColor(self.backgroundRole(), QColor(255, 255, 255))
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    windo = Img_viewed()
    windo.showMaximized()
    sys.exit(app.exec_())