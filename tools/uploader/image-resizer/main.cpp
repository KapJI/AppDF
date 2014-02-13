#include <QtCore>
#include <QImage>

class Task : public QObject
{
    Q_OBJECT
public:
    Task(QObject *parent = 0) : QObject(parent) {}

public slots:
    void run() {
        // Do processing here
        QStringList args = QCoreApplication::arguments();
        if (args.size() != 5) {
            qCritical() << "usage:" << args.at(0).toStdString().c_str() << "[image_path] [save_path] [new_width] [new_height]";
            emit finished();
            return;
        }
        QString filepath = args.at(1);
        QString savepath = args.at(2);
        QString width = args.at(3);
        QString height = args.at(4); 
        QImage img(filepath);
        if (img.isNull()) {
            qCritical() << "No such file";
            emit finished();
            return;
        }
        if (width.toUInt() == 0 || height.toUInt() == 0) {
            qCritical() << "Invalid size";
            emit finished();
            return;
        }
        QImage small = img.scaled(width.toUInt(), height.toUInt(), Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
        small.save(savepath);
        emit finished();
    }

signals:
    void finished();
};

#include "main.moc"

int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    // Task parented to the application so that it
    // will be deleted by the application.
    Task *task = new Task(&app);

    // This will cause the application to exit when
    // the task signals finished.    
    QObject::connect(task, SIGNAL(finished()), &app, SLOT(quit()));

    // This will run the task from the application event loop.
    QTimer::singleShot(0, task, SLOT(run()));
    return app.exec();
}
