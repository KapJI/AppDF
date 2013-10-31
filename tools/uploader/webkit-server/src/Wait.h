#include "SocketCommand.h"

class WebPageManager;

class Wait : public SocketCommand {
  Q_OBJECT

  public:
    Wait(WebPageManager *page, QStringList &arguments, QObject *parent = 0);
    virtual void start();

  private slots:
    void loadFinished(bool success);
};