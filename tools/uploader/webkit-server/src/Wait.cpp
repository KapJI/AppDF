#include "Wait.h"
#include "WebPageManager.h"
#include "WebPage.h"

Wait::Wait(WebPageManager *manager, QStringList &arguments, QObject *parent) : SocketCommand(manager, arguments, parent) 
{}

void Wait::start() {
  connect(page(), SIGNAL(pageFinished(bool)), this, SLOT(loadFinished(bool)));

  if (!manager()->isLoading()) {
    disconnect(page(), SIGNAL(pageFinished(bool)), this, SLOT(loadFinished(bool)));
    finish(true);
  }
}

void Wait::loadFinished(bool success) {
  QString message;
  if (!success)
    message = page()->failureString();

  disconnect(page(), SIGNAL(pageFinished(bool)), this, SLOT(loadFinished(bool)));
  finish(success, message);
}