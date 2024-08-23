from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QDoubleSpinBox,
    QTimeEdit,
    QDateTimeEdit,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QComboBox,
    QLineEdit,
    QSlider
)
from qtwidgets import Toggle

class InterfaceUtils:
    
    # Sets the fonts used in the interface
    def set_fonts(window):
        window.main_font = QtGui.QFont(str("Initial Font"), 10)
        window.main_font.setBold(True)
        window.features_font = QtGui.QFont(str(window.main_font), 8)
        window.features_font.setBold(True) 
        
    # The messageBox appears with specific title and content
    def pop_message(title, content):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowIcon(QtGui.QIcon('./Resources//SNOOKER.ico'))   
        msg.setText(content)         
        msg.exec_()
    
    # Sets the style used in the interface
    def set_widgets_style(window, path): 
        with open(path,"r") as fh:
            window.setStyleSheet(fh.read())
            
    # Updates window size
    def update_window_size(window, index):
        #print(index)
        for i in range(window.tabs.count()):
            if i != index:
                window.tabs.widget(i).setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        window.tabs.widget(index).setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        window.tabs.widget(index).resize(window.tabs.widget(index).minimumSizeHint())
        window.tabs.widget(index).adjustSize()
        
        for i in range(0,20):
            QApplication.processEvents()
        #print("Aqui", self.minimumSizeHint())
        window.resize(window.minimumSizeHint())
        
    # Creates groupbox widget
    def create_groupbox(window, name, layout, font, enabled):
                        
        groupbox = QGroupBox(name, window)
        groupbox.setLayout(layout)
        groupbox.setFont(font)
        groupbox.setEnabled(enabled)
        return groupbox
    
    # Creates doublespin widget
    def create_doublespin(window, min_range, max_range, single_step, value):
        
        double_spin_box = QDoubleSpinBox(window)
        double_spin_box.setRange(min_range, max_range) 
        double_spin_box.setSingleStep(single_step)
        double_spin_box.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        double_spin_box.setAlignment(QtCore.Qt.AlignHCenter) 
        double_spin_box.setValue(value)
        return double_spin_box
    
    # Creates toogle widget
    def create_toogle(checked):
        
        toogle = Toggle()
        toogle.setChecked(checked)
        return toogle
    
    # Creates timedit widget
    def create_timedit(window, time, object_name, display_format):
        
        time_edit = QTimeEdit(window)
        time_edit.setTime(time)
        time_edit.setObjectName(object_name)
        time_edit.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        time_edit.setDisplayFormat(display_format)
        return time_edit
    
    # Creates datetimedit widget
    def create_datetimedit(datetime, display_format, font, popup):
        
        date = QDateTimeEdit()
        date.setDisplayFormat(display_format)
        date.setFont(font)
        date.setDateTime(datetime)
        date.setCalendarPopup(popup)
        return date
    
    # Creates button widget
    def create_button(window, name, object_name, _property):
        
        button = QPushButton(name, window) 
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        if object_name != None:
            button.setObjectName(object_name)
        if _property != None:
            button.setProperty(_property, True)
        return button
    
    # Creates checkbox widget
    def create_checkbox(name, object_name, checked):
        
        checkbox = QCheckBox(name)
        if object_name != None:
            checkbox.setObjectName(object_name)
        checkbox.setChecked(checked)
        checkbox.setLayoutDirection(QtCore.Qt.RightToLeft) 
        return checkbox
    
    # Creates radiobox widget
    def create_radiobox(name, checked):
        
        radiobox = QRadioButton(name)
        radiobox.setChecked(checked)
        radiobox.setLayoutDirection(QtCore.Qt.RightToLeft) 
        return radiobox
    
    # Creates combox widget
    def create_combox(params):
        
        combo_box = QComboBox()     
        if params != None:
            combo_box.addItems(params)
        return combo_box
    
    # Creates linedit widget
    def create_linedit(text, object_name, validator, font):
        
        line_edit = QLineEdit()
        line_edit.setText(text)
        line_edit.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        line_edit.setFont(font)
        if object_name != None:
            line_edit.setObjectName(object_name)
        if validator != None:    
            line_edit.setValidator(validator)
        return line_edit
    
    # Creates slider widget
    def create_slider(orientation, min_range, max_range, value, interval):
        
        slider = QSlider(orientation)
        slider.setMinimum(min_range)
        slider.setMaximum(max_range)
        slider.setValue(value)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(interval)
        return slider