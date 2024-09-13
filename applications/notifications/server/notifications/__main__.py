from notifications.controllers.notifications_controller import NotificationsController


def main():
    nc = NotificationsController()
    nc.start_handlers()


if __name__ == '__main__':
    main()
