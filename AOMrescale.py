# AOMrescale.py
# Ted Corcovilos (20130312)
# Rescale the AOM calibration files so that we only have to measure the maximum power
# listfile contains definitions of the AOM channels
# logfile contains a log of the updated values

# TODO:
# Option to scale relative to arbitrary point
# Handle the Lattice files to account for their dependencies

import Tkinter as Tk
import tkFileDialog, tkMessageBox, tkSimpleDialog
import os,csv,shutil,datetime

# Global variables

listfilename = "aomlist.txt" # stores the filenames and reloads next time
logfile = "aomlog.txt" # log file of update values
widthNew = 8 # Width of "new value" field
widthFile = 30 # width of filename field

# Function declarations
def readfile(filename):
    x = []
    y = []
    file = open(filename,mode='rb')
    reader = csv.reader(file,delimiter='\t')

    for i in reader:
        data = i
        x.append(float(data[0]))
        y.append(float(data[1]))
    file.close()
    return x, y

def format_logvalue(value):
    # Format a value for the log with one decimal place, adding more places
    # only if they are needed to represent the value exactly (capped at 6).
    for prec in xrange(1, 7):
        s = "%.*f" % (prec, value)
        if float(s) == value:
            return s
    return "%.6f" % value

class App:
    def __init__(self,master):
        self.master = master
        self.frame = Tk.Frame(master)
        self.frame.grid()

        # per-channel state (parallel lists, one entry per AOM row).
        # Rows are created by add_row(), which appends to each of these.
        self.Number = 0
        self.Names = []
        self.AOMfile = []
        self.minvalue = []
        self.enableFile = []
        self.enableFileValue = []
        self.fileEntry = []
        self.fileButton = []
        self.oldLabel = []
        self.oldLabelText = []
        self.oldvalues = []
        self.newEntry = []
        self.newvalues = []
        self.newvaluetext = []
        self.yvalues = []
        self.xvalues = []
        self.newmintext = []
        self.minEntry = []
        self.nameLabel = []

        # Label row
        Tk.Label(self.frame,text="Enable").grid(row=0,column=0)
        Tk.Label(self.frame,text="AOM").grid(row=0,column=1)
        Tk.Label(self.frame,text="File").grid(row=0,column=2)
        Tk.Label(self.frame,text="Old max\nvalue").grid(row=0,column=5)
        Tk.Label(self.frame,text="New max\nvalue").grid(row=0,column=6)
        Tk.Label(self.frame,text="Min value\nof max").grid(row=0,column=7)

        self.vcmd = (self.frame.register(self.OnValidate),
                     '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # Load the saved channel definitions and build a row for each.
        if os.path.isfile(listfilename):
            for name, fname, minval in self.readlistfile():
                self.add_row(name, fname, minval)
        else:
            tkMessageBox.showerror("File error","Unable to locate list file:\n{0:s}".format(listfilename))
            self.frame.quit()

        # Define buttons
        self.buttonframe = Tk.Frame(self.frame)

        self.QuitButton = Tk.Button(self.buttonframe,text="Quit",command=self.frame.quit)
        self.QuitButton.grid(row=0,column=0,padx=10)

        self.ResetButton = Tk.Button(self.buttonframe,text="Load old values",command=self.reset)
        self.ResetButton.grid(row=0,column=1,padx=10)

        self.AddButton = Tk.Button(self.buttonframe,text="Add AOM",command=self.addAOM)
        self.AddButton.grid(row=0,column=2,padx=10)

        self.SaveButton = Tk.Button(self.buttonframe,text="Save filenames",command=self.writelistfile)
        self.SaveButton.grid(row=0,column=3,padx=10)

        self.UpdateButton = Tk.Button(self.buttonframe,text="Update calibration",command=self.update)
        self.UpdateButton.grid(row=0,column=4,padx=10)

        self.reposition_buttons()

    def add_row(self, name, fname, minval, enabled=0):
        # Build one AOM row and append its state/widgets to the parallel lists.
        # Used both at startup (one call per line of the list file) and by the
        # "Add AOM" button at runtime.
        i = self.Number

        # per-channel state
        v = Tk.StringVar(); v.set(name);   self.Names.append(v)
        v = Tk.StringVar(); v.set(fname);  self.AOMfile.append(v)
        v = Tk.DoubleVar(); v.set(minval); self.minvalue.append(v)
        self.enableFileValue.append(Tk.BooleanVar(value=enabled))
        self.oldLabelText.append(Tk.StringVar())
        self.oldvalues.append(Tk.DoubleVar())
        self.newvalues.append(Tk.DoubleVar())
        self.newvaluetext.append(Tk.StringVar())
        self.newmintext.append(Tk.StringVar())
        self.xvalues.append([])
        self.yvalues.append([])

        # enable checkbox
        cb = Tk.Checkbutton(self.frame,variable=self.enableFileValue[i])
        cb.grid(row=i+2,column=0)
        self.enableFile.append(cb)
        self.enableFileValue[i].trace_variable('w',lambda name, index, mode, j=i: self.callbackEnable(j))
        # row label
        lbl = Tk.Label(self.frame,textvariable=self.Names[i])
        lbl.grid(row=i+2,column=1)
        self.nameLabel.append(lbl)
        # filename field
        ent = Tk.Entry(self.frame,textvariable=self.AOMfile[i],width=widthFile,justify=Tk.RIGHT)
        ent.grid(row=i+2,column=2)
        self.fileEntry.append(ent)
        # browse button
        btn = Tk.Button(self.frame,text=" ",command=lambda j=i: self.pickfile(j))
        btn.grid(row=i+2,column=3,sticky=Tk.W)
        self.fileButton.append(btn)
        # old max value label
        self.oldLabelText[i].set("0.00")
        ol = Tk.Label(self.frame,textvariable=self.oldLabelText[i])
        ol.grid(row=i+2,column=5)
        self.oldLabel.append(ol)
        # new max value entry
        ne = Tk.Entry(self.frame,textvariable=self.newvaluetext[i],
                      validate="key",validatecommand=self.vcmd,
                      justify=Tk.CENTER,width=widthNew)
        ne.grid(row=i+2,column=6)
        self.newEntry.append(ne)
        self.newvaluetext[i].trace_variable('w',lambda name, index, mode, j=i: self.callbackNewValues(j))
        # min value label
        ml = Tk.Label(self.frame,textvariable=self.newmintext[i])
        ml.grid(row=i+2,column=7)
        self.minEntry.append(ml)
        self.newmintext[i].set("{0:.3f}".format(self.minvalue[i].get()))
        self.newmintext[i].trace_variable('w',lambda name, index, mode, j=i: self.callbackminvalue(j))

        self.Number = self.Number + 1
        self.callbackEnable(i) # set enabled/disabled state of the row
        return

    def reposition_buttons(self):
        # Keep the button bar directly below the (variable number of) AOM rows.
        self.buttonframe.grid(row=self.Number+2, column=0, columnspan=8)
        return

    def addAOM(self):
        name = tkSimpleDialog.askstring("Add AOM","Name for the new AOM channel:",parent=self.frame)
        if not name:
            return # cancelled or empty
        minval = tkSimpleDialog.askfloat("Add AOM","Minimum value of max (0 for none):",
                                         parent=self.frame,initialvalue=0.0)
        if minval is None:
            minval = 0.0
        # New row starts enabled and with an empty file; the user picks the
        # calibration file with its Browse button, then "Save filenames".
        self.add_row(name,"",minval,enabled=1)
        self.reposition_buttons()
        tkMessageBox.showinfo("Add AOM",
                              "Added '{0:s}'.\n\nClick its Browse button to choose the "
                              "calibration file, then 'Save filenames' to keep it.".format(name))
        return

    def reset(self):
        for i in xrange(self.Number):
            if (self.enableFileValue[i].get()):
                try:
                    self.xvalues[i], self.yvalues[i] = readfile(self.AOMfile[i].get())
                except IOError:
                    tkMessageBox.showerror("File error","Unable to open calibration file\n{0:s}".format(self.AOMfile[i].get()))
                    continue # skip this file, but keep loading the rest
                except ValueError:
                    tkMessageBox.showerror("File error","Unable to open calibration file\n{0:s}".format(self.AOMfile[i].get()))
                    continue # skip this file, but keep loading the rest
                ymax = max(self.yvalues[i])
                self.oldvalues[i].set(ymax)
                self.oldLabelText[i].set("{0:.2f}".format(ymax))
        return

    def update(self):
        for i in xrange(self.Number):
            if (self.enableFileValue[i].get() and os.path.isfile(self.AOMfile[i].get())):
                file = self.AOMfile[i].get()
                self.xvalues[i], self.yvalues[i] = readfile(file)
                # Read the current maximum directly from the file so that
                # repeated updates cannot compound the scaling (a re-run
                # scales by new/current == 1.0 and is therefore a no-op).
                oldmax = max(self.yvalues[i])
                if oldmax <= 0:
                    tkMessageBox.showerror("Value error",
                                           "Old value for {0:s} is invalid.\nDisabling this line".format(self.Names[i].get()))
                    self.enableFileValue[i].set(False)
                    continue
                if self.newvalues[i].get() <= 0:
                    tkMessageBox.showerror("Value error",
                                           "New value for {0:s} is invalid.\nDisabling this line".format(self.Names[i].get()))
                    self.enableFileValue[i].set(False)
                    continue
                scale = self.newvalues[i].get()/oldmax
                newx = self.xvalues[i]
                newy = [0]*len(newx) # initialize newy to a list of the right length
                for j in xrange(len(newx)):
                    newy[j] = self.yvalues[i][j]*scale
                # Create a backup file, but never overwrite an existing backup.
                # Overwriting would replace the pristine original with an
                # already-rescaled file on a second run, losing the original.
                bakfile = file+'.bak'
                if not os.path.isfile(bakfile):
                    try:
                        shutil.copyfile(file,bakfile)
                    except:
                        tkMessageBox.showerror("File error","Unable to create backup for\n{0:s}\nProceeding to next file.".format(file))
                        continue # skip this file if unable to create backup
                fh = open(file,'wb')
                w = csv.writer(fh,delimiter='\t',lineterminator='\r\n')
                for j in xrange(len(newy)):
                    w.writerow([newx[j],newy[j]])
                fh.close()
                # Reflect the new maximum in the display so it stays in sync
                # with the file that was just written.
                self.oldvalues[i].set(self.newvalues[i].get())
                self.oldLabelText[i].set("{0:.2f}".format(self.newvalues[i].get()))
        self.writelog(logfile)
        return

    def writelog(self, filename):
        # Build the header for the current channel set.  It is written both
        # when the log is first created and whenever the channel set changes,
        # so the columns never silently drift out of sync with the header.
        header = ["#Date"]
        for i in self.Names:
            header.append(i.get())
        need_header = True
        if os.path.isfile(filename):
            try:
                with open(filename,'rb') as fh:
                    last_header = None
                    for line in fh:
                        if line.startswith("#Date"):
                            last_header = line.rstrip("\r\n").split("\t")
                if last_header == header:
                    need_header = False
            except IOError:
                tkMessageBox.showerror("File error","Unable to read log file")
                return
        try:
            fh = open(filename,'ab')
        except IOError:
            tkMessageBox.showerror("File error","Unable to open log file")
            return
        try:
            w = csv.writer(fh,delimiter='\t')
            if need_header:
                w.writerow(header)
            row = [datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")]
            for i in xrange(self.Number):
                try:
                    value = float(self.newvaluetext[i].get())
                except Exception:
                    row.append('')
                else:
                    if self.enableFileValue[i].get():
                        row.append(format_logvalue(value))
                    else: # shouldn't happen, but just in case
                        row.append('')
            w.writerow(row)
        finally:
            fh.close()
        return

    def pickfile(self, i):
        file = tkFileDialog.askopenfilename(title="Calibration file for %s" % self.Names[i].get())
        if file: # askopenfilename returns '' if the dialog is cancelled
            self.AOMfile[i].set(os.path.normpath(file))
        return

    def callbackEnable(self, i):
        enabled = self.enableFileValue[i].get()
        if enabled:
            self.nameLabel[i].config(state=Tk.NORMAL)
            self.fileEntry[i].config(state=Tk.NORMAL)
            self.fileButton[i].config(state=Tk.NORMAL)
            self.oldLabel[i].config(state=Tk.NORMAL)
            self.newEntry[i].config(state=Tk.NORMAL)
            self.minEntry[i].config(state=Tk.NORMAL)
        else:
            self.nameLabel[i].config(state=Tk.DISABLED)
            self.fileEntry[i].config(state=Tk.DISABLED)
            self.fileButton[i].config(state=Tk.DISABLED)
            self.oldLabel[i].config(state=Tk.DISABLED)
            self.newEntry[i].config(state=Tk.DISABLED)
            self.minEntry[i].config(state=Tk.DISABLED)
        return

    def callbackNewValues(self, i):
        try:
            value = float(self.newvaluetext[i].get())
        except Exception:
            value = 0
        self.newvalues[i].set(value)
        if (value < self.minvalue[i].get()):
            # set color to red to notify user
            self.newEntry[i].config(fg='red')
        else:
            # set color to black
            self.newEntry[i].config(fg='black')
        return

    def callbackminvalue(self, i):
        try:
            value = float(self.newmintext[i].get())
        except Exception:
            value = 0
        self.minvalue[i].set(value)
        return

    def OnValidate(self, d, i, P, s, S, v, V, W):
        if P == '': # allow empty string to pass
            return True
        try:
            float(P)
            outcome = True
        except ValueError:
            outcome = False
        return outcome

    def readlistfile(self):
        # The listfile should be in the format:
        # name  filename    minimum value
        # Returns a list of (name, filename, minvalue) tuples.
        entries = []
        with open(listfilename,'rb') as file:
            r = csv.reader(file,delimiter='\t')
            r.next() # discard header row
            for i in r:
                if not i:
                    continue # skip blank lines
                name, fname, minval = i
                entries.append((name, fname, float(minval)))
        return entries

    def writelistfile(self):
        with open(listfilename,'wb') as file:
            w = csv.writer(file,delimiter='\t')
            w.writerow(["#Name","File","Min"])
            for i in xrange(self.Number):
                w.writerow([self.Names[i].get(),self.AOMfile[i].get(),self.minvalue[i].get()])
        return


# Main loop
root = Tk.Tk() # root window

app = App(root)

root.mainloop() # display window and run
