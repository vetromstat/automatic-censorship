import filetype 
import os
import sys
from scipy.io import wavfile
from designer import Ui_MainWindow
from PyQt6.QtCore import QThread,pyqtSignal,QObject,QUrl
from PyQt6 import QtWidgets,QtGui
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import wave
import json
import pydub as pd
from vosk import Model, KaldiRecognizer, SetLogLevel
import Word as custom_Word
import noisereduce as nr
"""
To do:  1) noise reduce(numba with python 3.11 )  
        2) marks 
 

"""
"""
            if timings[0][0] < position*1000 < timings[0][1]:
                self.ui.startlbl.setStyleSheet('''border: dotted;color: rgb(255, 0, 0);font: 63 8pt "Yu Gothic UI Semibold;''')
                print("YES")
            else:
                self.ui.startlbl.setStyleSheet('''border: dotted;color: rgb(255, 255, 255);font: 63 8pt "Yu Gothic UI Semibold;''')
"""
#верхняя граница герцовки  
high_gerz=500
#нижняя граница герцовки
low_gerz=2500
#точность > 50% 
confidience=0.5  
#Пути 
model_pathRU = r"C:\Users\Kravt\source\repos\speechless3\vosk-model-ru-0.22"
model_pathEN = r"C:\Users\Kravt\source\repos\speechless3\vosk-model-en-us-0.22"
model_pathENsmall = r"C:\Users\Kravt\source\repos\speechless3\vosk-model-en-us-0.22-lgraph"
model_pathRUsmall = r"C:\Users\Kravt\source\repos\speechless3\vosk-model-small-ru-0.22"
#имя файла звука,имя txt файла, язык, имя нового файла и путь, модель, имя нового файл, директория для сохранения, слова для удаления 

timings = []
audio_filename = ""
txt_filename = ""
model = Model(model_pathRUsmall)
new_audio = "/cenz.mp3"
new_dir = ""
words = ""
txt = ""
Threading = False 
sound = False
  
class Worker(QObject):
    finished = pyqtSignal()
    isRunning = True    
    def stop(self):
        self.isRunning = False
    def run(self):
        global audio_filename,txt_filename,sound,Threading,format,timings
        Threading = True
        sound = pd.AudioSegment.from_file(audio_filename)
        format = filetype.guess_extension(audio_filename)
        if format != "wav":
            sound.export(audio_filename+"TEMP.wav",format = "wav") 
            wf = wave.open(audio_filename+"TEMP.wav" , "rb")
        else:
            wf = wave.open(audio_filename , "rb")
        # load data
        '''
        rate, data = wavfile.read(audio_filename)
        print(rate,data)
        # perform noise reduction
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        wavfile.write(audio_filename + ".wav", rate, reduced_noise)
            #считываем файл                  + ".wav" некст строка
        '''
        
            #рекогнайзер
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        results = []
            #результат в джсон массив 
        print(wf.getnframes()/4000)
        while self.isRunning:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    results.append(part_result)
            part_result = json.loads(rec.FinalResult())
            results.append(part_result)

            list_of_words = []
            for sentence in results:
                if len(sentence) == 1:
                    continue
                for obj in sentence['result']:
                    w = custom_Word.Word(obj)  
                    list_of_words.append(w)
            start_timings_list = []
            end_timings_list = []
            for word in list_of_words:
                if word.word in words and word.conf>confidience : 
                    start_timings_list.append(word.start)
                    end_timings_list.append(word.end)
                    before = sound[:word.start*1000]
                    middle = sound[word.start*1000:word.end*1000]
                    after = sound[word.end*1000:]
                    middle =  pd.AudioSegment.silent(duration = word.end*1000 - word.start*1000)
                    sound = before + middle + after 
                print(word.to_string())
            timings = tuple(zip(start_timings_list,end_timings_list))
            print(timings)
            sound.export(audio_filename + "cenz." + format,format = format)
            MyWin.player.setSource(QUrl.fromLocalFile(audio_filename + "cenz." + format))
            wf.close()  
            if format != "wav":
                os.remove(audio_filename+"TEMP.wav")
            Threading = False
            self.finished.emit()
            return

def SetVisibility(self,arg):
    if arg:
        
        self.ui.crossbtn.setVisible(True)
        self.ui.playbtn.setVisible(True)
        self.ui.horizontalSlider.setVisible(True)
        self.ui.checkbtn.setVisible(True)
        self.ui.startlbl.setText("0:00")
    else:
        self.ui.crossbtn.setVisible(False)
        self.ui.playbtn.setVisible(False)
        self.ui.horizontalSlider.setVisible(False)
        self.ui.checkbtn.setVisible(False)
        self.ui.startlbl.setText("")

class MyWin(QtWidgets.QMainWindow):

    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    
    
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon("C:/Users/Kravt/source/repos/speechless3/icons/audio-censoring-website-favicon-color.png"))
        self.setWindowTitle("Censoring!")
        self.ui.DD.setAcceptDrops(True)
        self.ui.label.setVisible(False)
        self.ui.horizontalSlider.setVisible(False)
        self.ui.playbtn.setVisible(False)
        self.ui.iconbtn.clicked.connect(self.File)
        self.ui.wavpathbtn.clicked.connect(self.WavPath)
        self.ui.englishbtn.clicked.connect(self.EnFoo)
        self.ui.rusbtn.clicked.connect(self.RuFoo)
        self.ui.txtpathbtn.clicked.connect(self.TxtPath)
        self.ui.crossbtn.clicked.connect(self.Cross)
        self.ui.playbtn.clicked.connect(self.Play)
        self.ui.confirm.clicked.connect(self.Work)
        self.ui.checkbtn.clicked.connect(self.Check) 
        self.player.playbackStateChanged.connect(self.StoppedState)
        self.player.durationChanged.connect(self.DurationChanged)
        self.ui.horizontalSlider.valueChanged.connect(self.SetPosition)
        self.player.positionChanged.connect(self.AudioProgress)
        self.movie = QtGui.QMovie("C:/Users/Kravt/source/repos/speechless3/icons/Spinner-2.4s-300px.gif")
        self.ui.loadlbl.setMovie(self.movie)
        self.movie.start()
        SetVisibility(self,False)

    def Work(self):
        global words
        words += self.ui.textEdit.toPlainText()
        if not words:
            QMessageBox().warning(self,"Words to delete unidentified","Pick your words",QMessageBox.StandardButton.Ok)
            return

        self.Disable()
        self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.currentIndex() + 1)
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.Finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start() 

    def Finished(self):
        self.Enable()
        self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.currentIndex() - 1)
        self.ui.playbtn.setVisible(True)
        self.ui.label.setVisible(True)
        self.ui.checkbtn.setText("Censored")
        QMessageBox().information(self,"Complete!", "File saved to the same location, click logo to specify location",QMessageBox.StandardButton.Ok)

    def File(self):
        global new_dir,sound,format
        
        if not sound:
            return
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
        self,
        "Open a folder",) 
        if new_dir == "" : return
        self.player.setSource(QUrl.fromLocalFile(audio_filename))
        os.rename(audio_filename + "cenz." + format, new_dir + "/" + os.path.basename(audio_filename + "cenz." + format))
        self.player.setSource(QUrl.fromLocalFile(new_dir + "/" + os.path.basename(audio_filename + "cenz." + format)))

    def Cross(self):
        global audio_filename,new_dir,Threading,sound,start_timings_list,end_timings_list
        if Threading:
            self.worker.stop()
            self.thread.quit()
            self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.currentIndex() - 1)
            self.Enable()

        self.ui.wavurllbl.setText("")
        new_dir = ""
        audio_filename = ""
        sound = False
        start_timings_list = []
        end_timings_list = []
        self.ui.startlbl.setText("")
        self.ui.iconbtn.setStyleSheet("border:dotted;")
        self.ui.wavurllbl.setText("")
        self.ui.iconbtn.setText("Drop your file here")
        self.ui.label.setVisible(False)
        SetVisibility(self,False)
        sound = False
        self.player.stop()
        self.ui.endlbl.setText("")
        

    def EnFoo(self):
        global model
        model = Model(model_pathENsmall)

    def RuFoo(self):
        global model
        model = Model(model_pathRUsmall)

    def Disable(self):
        self.ui.wavpathbtn.setEnabled(False)
        self.ui.txtpathbtn.setEnabled(False)
        self.ui.textEdit.setEnabled(False)
        self.ui.rusbtn.setEnabled(False)
        self.ui.englishbtn.setEnabled(False)
        self.ui.confirm.setEnabled(False)
        self.ui.checkbtn.setEnabled(False)
        self.setAcceptDrops(False)
        
        

    def Enable(self):
        self.ui.wavpathbtn.setEnabled(True)
        self.ui.txtpathbtn.setEnabled(True)
        self.ui.textEdit.setEnabled(True)
        self.ui.rusbtn.setEnabled(True)
        self.ui.englishbtn.setEnabled(True)
        self.ui.confirm.setEnabled(True)
        self.ui.checkbtn.setEnabled(True)
        self.setAcceptDrops(True)



    def Check(self): 
        global sound
        if self.ui.checkbtn.isChecked():
            if sound:
                MyWin.player.setSource(QUrl.fromLocalFile(audio_filename))
                self.ui.checkbtn.setText("Uncesored")
            else: 
                return

        else:
            if sound:
                MyWin.player.setSource(QUrl.fromLocalFile(audio_filename + "cenz." + format))
                self.ui.checkbtn.setText("Censored")
            else: 
                return

 

    def WavPath(self):
        global audio_filename
        fname = QFileDialog.getOpenFileName(
            self, 
            "Open file",
            ".", 
            "Audio Files(*)") 
        print(fname[0])
        if fname[0] == "" : return
        audio_filename = fname[0]
        self.ui.iconbtn.setStyleSheet("border-image: url(C:/Users/Kravt/source/repos/rc6/rc6/3767084.png);")
        self.ui.wavurllbl.setText(audio_filename)
        self.ui.iconbtn.setMinimumWidth(150)
        self.ui.iconbtn.setText("")
        self.player.setSource(QUrl.fromLocalFile(audio_filename))
        SetVisibility(self,True)
        


    def TxtPath(self):
        fname = QFileDialog.getOpenFileName(
            self, 
            "Open file",
            ".", 
            "Text Files(*.txt)")
        global txt_filename,words
        if fname[0] == "" : return
        txt_filename = fname[0]
        words = ""
        with open(txt_filename,'r',encoding='utf-8-sig') as file: 
            for line in file:      
                for word in line.split():     
                    words+=word
        self.ui.txturllbl.setText(txt_filename)
            
    def dragEnterEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if event.mimeData().hasUrls():
            print(filetype.is_audio(files[0]), files[0],len(files))
            if len(files) == 1 and filetype.is_audio(files[0]):
                event.accept()
            else:
                event.ignore()
        else:
                event.ignore()
               
    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        global words
        words = self.ui.textEdit.toPlainText()
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        global audio_filename
        audio_filename = files[0]
        self.ui.wavurllbl.setText(audio_filename)
        self.player.setSource(QUrl.fromLocalFile(audio_filename))
        self.ui.iconbtn.setStyleSheet("border-image: url(C:/Users/Kravt/source/repos/rc6/rc6/3767084.png);")
        self.ui.iconbtn.setMinimumWidth(150)
        self.ui.iconbtn.setText("")
        SetVisibility(self,True)

    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                         "QUIT",
                                         "Are you sure you want to quit ?",
                                         QMessageBox.StandardButton.Yes  | QMessageBox.StandardButton.No)

        if close == QMessageBox.StandardButton.Yes:
            if Threading:
                self.worker.stop()
                self.thread.quit()
                self.thread.wait()
                event.accept()
            else:
                event.accept()
        else:
                event.ignore()


    def SetPosition(self):
        self.player.setPosition(self.sender().value())

    def AudioProgress(self,position):
        
        self.ui.horizontalSlider.setValue(position)
        
        if position%60000 > 10000:
            self.ui.startlbl.setText(str(position//60000)+":"+str((position%60000)//1000))
        else:
            self.ui.startlbl.setText(str(position//60000)+":"+"0"+str((position%60000)//1000))
        

    def DurationChanged(self):
         print(self.player.duration())
         if self.player.duration()%60000 > 10000:
            self.ui.endlbl.setText(str(self.player.duration()//60000)+":"+str((self.player.duration()%60000)//1000))
         else:
            self.ui.endlbl.setText(str(self.player.duration()//60000)+":"+"0"+str((self.player.duration()%60000)//1000))
         self.ui.horizontalSlider.setRange(0,self.player.duration())
         self.ui.horizontalSlider.setValue(0)

    def StoppedState(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            self.ui.playbtn.setStyleSheet("border-image: url(C:/Users/Kravt/source/repos/speechless3/icons/play2.png);")

    def Play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState or self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
            self.ui.playbtn.setStyleSheet("border-image: url(C:/Users/Kravt/source/repos/speechless3/icons/pause.png);")
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.ui.playbtn.setStyleSheet("border-image: url(C:/Users/Kravt/source/repos/speechless3/icons/play2.png);")

   
def main():

    app = QtWidgets.QApplication(sys.argv)
    window = MyWin()
    window.show()  
    sys.exit( app.exec() )
   
if __name__=="__main__":
    main()
