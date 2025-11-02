# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 10:49:57 2021

@author: Leonardo Ferreira
@goal: Useful functions for the interfaces used
"""

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
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
    def set_fonts(window):
        """
        Sets the fonts used in the interface.

        Parameters
        ----------
        window : window
            Window where the fonts are applied.

        Returns
        -------
        None.

        """
        window.main_font = QtGui.QFont(str("Initial Font"), 10)
        window.main_font.setBold(True)
        window.features_font = QtGui.QFont(str(window.main_font), 8)
        window.features_font.setBold(True) 
        
    def pop_message(title, content):
        """
        The message box appears with specific title and content.

        Parameters
        ----------
        title : str
            Title of the message box.
        content : str
            Content of the message box.

        Returns
        -------
        None.

        """
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowIcon(QtGui.QIcon('./Resources//tkinter_icon.ico'))   
        msg.setText(content)         
        msg.exec_()
    
    def set_widgets_style(window, path): 
        """
        Sets the style used in the interface.

        Parameters
        ----------
        window : window
            Window where the style of the widgets is applied.
        path : str
            Path of the style file.

        Returns
        -------
        None.

        """
        with open(path,"r") as fh:
            window.setStyleSheet(fh.read())
        
    def create_groupbox(window, name, layout, font, enabled):
        """
        Creates groupbox widget.

        Parameters
        ----------
        window : window
            Window where the group box is built.
        name : str
            Name of the group box.
        layout : multiple types of layout (QHBoxLayout, QVBoxLayout, among others)
            Layout of the group box.
        font : str
            Font of the group box.
        enabled : bool
            Enabled or not.

        Returns
        -------
        groupbox : QGroupBox
            QGroupBox built.

        """
        groupbox = QGroupBox(name, window)
        groupbox.setLayout(layout)
        groupbox.setFont(font)
        groupbox.setEnabled(enabled)
        return groupbox
    
    def create_doublespin(window, min_range, max_range, single_step, value):
        """
        Creates doublespin widget.

        Parameters
        ----------
        window : window
            Window where the doublespin widget is built.
        min_range : int
            Minimum value of the doublespin.
        max_range : int
            Maximum value of the doublespin.
        single_step : float
            Step increment of the doublespin.
        value : float
            Current value of the doublespin.

        Returns
        -------
        double_spin_box : QDoubleSpinBox
            QDoubleSpinBox built.

        """
        double_spin_box = QDoubleSpinBox(window)
        double_spin_box.setRange(min_range, max_range) 
        double_spin_box.setSingleStep(single_step)
        double_spin_box.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        double_spin_box.setAlignment(QtCore.Qt.AlignHCenter) 
        double_spin_box.setValue(value)
        return double_spin_box
    
    def create_toogle(checked):
        """
        Creates toogle widget.

        Parameters
        ----------
        checked : bool
            If the toogle is checked or not.

        Returns
        -------
        toogle : Toggle
            Toggle built.

        """    
        toogle = Toggle()
        toogle.setChecked(checked)
        return toogle
    
    def create_timedit(window, time, object_name, display_format):
        """
        Creates timedit widget.

        Parameters
        ----------
        window : window
            Window where the timedit widget is built.
        time : QTime
            Time of the widget.
        object_name : str
            Name of the widget.
        display_format : str
            Display format of the time.

        Returns
        -------
        time_edit : QTimeEdit
            QTimeEdit built.

        """
        time_edit = QTimeEdit(window)
        time_edit.setTime(time)
        time_edit.setObjectName(object_name)
        time_edit.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        time_edit.setDisplayFormat(display_format)
        return time_edit
    
    def create_datetimedit(datetime, display_format, font, popup):
        """
        Creates datetimedit widget.

        Parameters
        ----------
        datetime : datetime
            Datetime of the widget.
        display_format : str
            Display format of the datetime.
        font : str
            Font of the datetimedit widget.
        popup : bool
            If it shows a new panel with datetime selection.

        Returns
        -------
        date : QDateTimeEdit
            QDateTimeEdit built.

        """
        date = QDateTimeEdit()
        date.setDisplayFormat(display_format)
        date.setFont(font)
        date.setDateTime(datetime)
        date.setCalendarPopup(popup)
        return date
    
    def create_button(window, name, object_name, _property):
        """
        Creates button widget.

        Parameters
        ----------
        window : window
            Window where the button widget is built.
        name : str
            Button name.
        object_name : str
            Name of the widget.
        _property : str
            Property for defining different styles of the button.

        Returns
        -------
        button : QPushButton
            QPushButton built.

        """
        button = QPushButton(name, window) 
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        if object_name != None:
            button.setObjectName(object_name)
        if _property != None:
            button.setProperty(_property, True)
        return button
    
    def create_checkbox(name, object_name, checked):
        """
        Creates checkbox widget.

        Parameters
        ----------
        name : str
            Checkbox name.
        object_name : str
            Name of the widget.
        checked : bool
            If it is checked or not.

        Returns
        -------
        checkbox : QCheckBox
            QCheckBox built.

        """
        checkbox = QCheckBox(name)
        if object_name != None:
            checkbox.setObjectName(object_name)
        checkbox.setChecked(checked)
        checkbox.setLayoutDirection(QtCore.Qt.RightToLeft) 
        return checkbox
    
    def create_radiobox(name, checked):
        """
        Creates radiobox widget.

        Parameters
        ----------
        name : str
            QRadioButton name.
        checked : bool
            If it is checked or not.

        Returns
        -------
        radiobox : QRadioButton
            QRadioButton built.

        """
        radiobox = QRadioButton(name)
        radiobox.setChecked(checked)
        radiobox.setLayoutDirection(QtCore.Qt.RightToLeft) 
        return radiobox
    
    def create_combox(params):
        """
        Creates combox widget.    

        Parameters
        ----------
        params : list
            List of the options available.

        Returns
        -------
        combo_box : QComboBox
            QComboBox built.

        """
        combo_box = QComboBox()      
        combo_box.addItems(params)
        return combo_box
    
    def create_linedit(text, object_name, validator, font):
        """
        Creates linedit widget.

        Parameters
        ----------
        text : str
            QlineEdit content.
        object_name : str
            Name of the widget.
        validator : QIntValidator
            QIntValidator applied for content validation.
        font : str
            Font of the QLineEdit.

        Returns
        -------
        line_edit : QLineEdit
            QLineEdit built.

        """      
        line_edit = QLineEdit()
        line_edit.setText(text)
        line_edit.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if font != None:
            line_edit.setFont(font)
        if object_name != None:
            line_edit.setObjectName(object_name)
        if validator != None:    
            line_edit.setValidator(validator)
        return line_edit
    
    def create_slider(orientation, min_range, max_range, value, interval):
        """
        Creates slider widget.

        Parameters
        ----------
        orientation : multiple options (Horizontal and Vertical)
            Slider Orientation.
        min_range : int
            Minimum value of the slider.
        max_range : int
            Maximum value of the slider.
        value : float
            Current value of the slider.
        interval : float
            Interval between values.

        Returns
        -------
        slider : QSlider
            QSlider built.

        """    
        slider = QSlider(orientation)
        slider.setMinimum(min_range)
        slider.setMaximum(max_range)
        slider.setValue(value)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(interval)
        return slider