from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt

import sys
  
# creating checkable combo box class
class CheckableComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
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
  
    # when any item get pressed
    def handle_item_pressed(self, index):
  
        # getting which item is pressed
        item = self.model().itemFromIndex(index)
        # make it check if unchecked and vice-versa
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self._changed = True
  
        # calling method
        if self.type == "analyst" or self.type == "families":            
            self.check_items()
        
    def hidePopup(self):
        if not self._changed:
            super(CheckableComboBox, self).hidePopup()
        self._changed = False
  
    # method called by check_items
    def item_checked(self, index):
  
        # getting item at index
        item = self.model().item(index, 0)
        # return true if checked else false
        return item.checkState() == Qt.Checked
    
    def get_items_checked(self):
        
        checked_items = []
        
        for i in range(self.count()):
            if self.item_checked(i):
                checked_items.append(i)
                
        return checked_items
  
    # calling method
    def check_items(self):
        #print("Aqui", self.limit)
        for i in range(self.count()):
            item = self.model().item(i, 0)
            if len(self.get_items_checked()) >= self.limit:
                if not self.item_checked(i):
                    item.setEnabled(False)
            else:
                item.setEnabled(True)
                
    def reset_items(self):
        for i in range(self.count()):
            item = self.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)
            item.setEnabled(True)
  
    # method to update the label
    def update_labels(self, item_list):
  
        n = ''
        count = 0
  
        # traversing the list
        for i in item_list:
            # if count value is 0 don't add comma
            if count == 0:
                n += ' % s' % i
            # else value is greater then 0
            # add comma
            else:
                n += ', % s' % i
            # increment count
            count += 1
  
        # loop
        for i in range(self.count()):
            # getting label
            text_label = self.model().item(i, 0).text()
            # default state
            if text_label.find('-') >= 0:
                text_label = text_label.split('-')[0]
            # shows the selected items
            item_new_text_label = text_label + ' - selected index: ' + n
           # setting text to combo box
            self.setItemText(i, item_new_text_label)
    # flush
    sys.stdout.flush()