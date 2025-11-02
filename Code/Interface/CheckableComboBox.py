"""
Created on Sun Mar 28 10:05:48 2021

@author: www.geeksforgeeks.org
@goal: Special widget for the interface
"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt

import sys
  
class CheckableComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        """
        Checkable ComboBox widget.

        Parameters
        ----------
        *args : multiple types
            Can have multiple arguments.
        **kwargs : can have multiple contents
            Content of the variables to be updated.

        Returns
        -------
        None.

        """
        super(CheckableComboBox, self).__init__()        
        
        self.args = args
        self.kwargs = kwargs
        self.type = self.args[0]
        if args[1] != None:
            self.limit = self.args[1]
        else:
            self.limit = sys.maxsize
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))
        self._changed = False
  
    def handle_item_pressed(self, index):
        """
        Handler for when any item get pressed.      

        Parameters
        ----------
        index : int
            Item index pressed.

        Returns
        -------
        None.

        """
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self._changed = True
  
        if self.type == "analyst" or self.type == "families":            
            self.check_items()
        
    def hidePopup(self):
        """
        Hides popup.

        Returns
        -------
        None.

        """
        if not self._changed:
            super(CheckableComboBox, self).hidePopup()
        self._changed = False
  
    def item_checked(self, index):
        """
        Checks state of item.

        Parameters
        ----------
        index : TYPE
            DESCRIPTION.

        Returns
        -------
        bool
            True if checked; False if unchecked.

        """
        item = self.model().item(index, 0)
        return item.checkState() == Qt.Checked
    
    def get_items_checked(self):
        """
        Gets items checked.

        Returns
        -------
        checked_items : list
            List of item checked.

        """
        checked_items = []
        
        for i in range(self.count()):
            if self.item_checked(i):
                checked_items.append(i)
                
        return checked_items
  
    def check_items(self):
        """
        Check items checked.

        Returns
        -------
        None.

        """
        for i in range(self.count()):
            item = self.model().item(i, 0)
            if len(self.get_items_checked()) >= self.limit:
                if not self.item_checked(i):
                    item.setEnabled(False)
            else:
                item.setEnabled(True)
                
    def reset_items(self):
        """
        Resets the state of items to unchecked

        Returns
        -------
        None.

        """
        for i in range(self.count()):
            item = self.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)
            item.setEnabled(True)
  
    def update_labels(self, item_list):
        """
        Updates the labels of items.

        Parameters
        ----------
        item_list : list
            List of items to update.

        Returns
        -------
        None.

        """
        n = ''
        count = 0
  
        for i in item_list:
            if count == 0:
                n += ' % s' % i
            else:
                n += ', % s' % i
            count += 1
  
        for i in range(self.count()):
            text_label = self.model().item(i, 0).text()
            if text_label.find('-') >= 0:
                text_label = text_label.split('-')[0]
            item_new_text_label = text_label + ' - selected index: ' + n
            self.setItemText(i, item_new_text_label)
    sys.stdout.flush()