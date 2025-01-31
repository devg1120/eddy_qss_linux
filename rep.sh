
#find ./ -type f -name "*.py" 
#find ./ -type f -name "*.py" | xargs sed -i -e "s/PyQt5/PySide6/g"
#find ./ -type f -name "*.py" | xargs sed -i -e "s/pyqtSignal/Signal/g"
#find ./ -type f -name "*.py" | xargs sed -i -e "s/pyqtSlot/Slot/g"
find ./ -type f -name "*.py" | xargs sed -i -e "s/QtWidgets\.QAction/QtGui\.QAction/g"
