import os
import pickle
import sys
from qtpy import QtGui, QtWidgets

class MyTable(QtWidgets.QTableWidget):
    def __init__(self, r, c, parent):
        super().__init__(r, c)
        self.check_change = True
        self.init_ui()
        self.parent = parent

    def init_ui(self):
        self.cellChanged.connect(self.c_current)
        self.cellClicked.connect(self.c_clicked)
        self.show()
        for i in range(0,self.columnCount()):
            self.setColumnWidth(i,150)

    def c_clicked(self):
        if self.currentColumn() == 5:
            text = QtWidgets.QInputDialog.getInt(self,"Enter Relist Fee",
                                                 "relist fee amount:")
            value = self.item(self.currentRow(), 0)
            self.parent.market_data[value.text()].relist_fee += text[0]
            self.parent.load_market_item(self.parent.market_data[value.text(

            )],self.currentRow())

    def c_current(self):
        if self.check_change:
            row = self.currentRow()
            col = self.currentColumn()
            value2 = self.item(row, col)
            if col == self.columnCount() - 1:
                try:
                    sstock = int(value2.text())
                    value = self.item(row, 1)
                    buyq = int(value.text())
                    value = self.item(row, 3)
                    sellq = int(value.text())
                    self.item(row,col-1).setText(str(buyq-sellq+sstock))
                    value = self.item(row,0)
                    self.parent.market_data[value.text()].base_stock = sstock
                except:
                    self.item(row,col).setText("Invalid")
            # elif col == 5:
            #     value = self.item(row, 0)
            #     self.parent.market_data[value.text()].relist_fee += \
            #         int(value2.text())
            #     self.parent.load_market_item(self.parent.market_data[value.text()],row)

    def set_row(self, data, row):
        for i in range(0,len(data)):
            self.setItem(row, i, QtWidgets.QTableWidgetItem(
                str(data[i])))


class MarketItem:

    buy_quantity = 0
    name = ''
    buy_price = 0
    buy_total_price = 0
    sell_quantity = 0
    sell_price = 0
    sell_total_price = 0
    base_stock = 0
    dates = set()
    relist_fee = 0

    def __init__(self, data):
        quant = int(data[1])
        self.name = data[2]
        self.dates.add(data[0])
        if int(data[4].split(" ")[0].replace(",","")) > 0:
            #print("Found first sell for "+self.name)
            self.sell_price = int(data[3].split(" ")[0].replace(",",""))
            self.sell_quantity = quant
            self.sell_total_price = self.sell_price*self.sell_quantity
        else:
            #print("Found first buy for " + self.name)
            self.buy_price = int(data[3].split(" ")[0].replace(",", ""))
            self.buy_quantity = quant
            self.buy_total_price = self.buy_price * self.buy_quantity

    def add(self, data):
        if data[0] not in self.dates:
            self.dates.add(data[0])
            new_quant = int(data[1])
            new_price = int(data[3].split(" ")[0].replace(",",""))

            if int(data[4].split(" ")[0].replace(",","")) > 0:
                self.sell_price = (self.sell_total_price + (new_price*new_quant))/(
                        new_quant+self.sell_quantity)
                self.sell_quantity += new_quant
                self.sell_total_price = self.sell_price * self.sell_quantity
            else:
                self.buy_price = (self.buy_total_price + (
                            new_price * new_quant)) / (
                                          new_quant + self.buy_quantity)
                self.buy_quantity += new_quant
                self.buy_total_price = self.buy_price * self.buy_quantity

class Example(QtWidgets.QMainWindow):

    raw_market_data = []
    market_data = {}
    sales_tax = 0.0225
    brokers_fee = 0.035

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def load(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setDefaultSuffix('market')
        path = dialog.getOpenFileName(self, 'Open Market Data',
                                                     os.getenv(
            'HOME'),
                                    'market(*.market)')
        if path[0] != '':
            with open(path[0],'rb') as f:
                self.market_data = pickle.load(f)
            self.load_market_data()

    def load_market_item(self, i, row):
        self.form_widget.check_change = False
        data = []

        data.append(i.name)
        data.append(i.buy_quantity)
        data.append(i.buy_price)
        data.append(i.sell_quantity)
        data.append(i.sell_price)
        relist_fee = i.relist_fee
        data.append(relist_fee)
        fees = i.sell_price * self.sales_tax + i.sell_price * self.brokers_fee + i.buy_price * self.brokers_fee
        data.append(fees)
        data.append(i.sell_price - i.buy_price - fees)
        data.append((i.sell_price - i.buy_price) * i.sell_quantity)
        data.append(
            (i.sell_price - i.buy_price - fees) * i.sell_quantity - relist_fee)
        base_stock = i.base_stock
        stock = i.buy_quantity - i.sell_quantity + base_stock
        data.append(stock)
        data.append(base_stock)

        self.form_widget.set_row(data, row)

        self.form_widget.check_change = True

    def load_market_data(self):
        self.form_widget.check_change = False
        self.form_widget.setRowCount(0)
        for key in self.market_data:
            i: MarketItem = self.market_data[key]
            row = self.form_widget.rowCount()
            self.form_widget.insertRow(row)
            self.load_market_item(i, row)
        self.form_widget.check_change = True

    def save(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setDefaultSuffix('market')
        dialog.setWindowTitle("Save Market Data")
        dialog.setDirectory(os.getenv('HOME'))
        dialog.setNameFilter('market(*.market)')
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        path = dialog.exec()
        if path == QtWidgets.QFileDialog.Accepted:
            with open(dialog.selectedFiles()[0],'wb') as f:
                pickle.dump(self.market_data,f)

    def initUI(self):
        self.setGeometry(0, 0, 960, 540)
        self.setWindowTitle('Evecountant')
        self.setWindowIcon(QtGui.QIcon('web.png'))
        self.center()

        exitAction = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        importAction = QtWidgets.QAction(QtGui.QIcon('import.png'), '&Import',
                                         self)
        importAction.setShortcut('Ctrl+I')
        importAction.setStatusTip('Import Market Data')
        importAction.triggered.connect(self.importData)

        saveAction = QtWidgets.QAction('&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.save)

        loadAction = QtWidgets.QAction('&Load', self)
        loadAction.setShortcut('Ctrl+L')
        loadAction.setStatusTip('Load')
        loadAction.triggered.connect(self.load)

        self.form_widget = MyTable(0, 12, self)
        self.setCentralWidget(self.form_widget)
        col_headers = ['Name', 'Buy Quantity', 'Buy Item Price',
                       'Sell Quantity',
                       'Sell Item Price', 'Relist Fee', 'Fees',
                       'Item Profit', 'Pre-Fees Profit', 'Profit', 'Stock',
                       'Starting Stock']
        self.form_widget.setHorizontalHeaderLabels(col_headers)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(importAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(loadAction)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)

        self.show()
        self.statusBar()

    def importData(self):
        text = QtWidgets.QInputDialog.getMultiLineText(self, "Import Market "
                                                           "Data",
                                                "Market Data:", "");

        if (text[1]):
            self.raw_market_data = text[0].split('\n')
            self.raw_market_data = [x.split('\t') for x in
                                    self.raw_market_data]
            for i in self.raw_market_data:
                if i[2] in self.market_data:
                    self.market_data[i[2]].add(i)
                else:
                    self.market_data[i[2]] = MarketItem(i)
        self.load_market_data()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()