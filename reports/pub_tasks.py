from common.pub_tasks import publish


def publish_report(data):
    publish('report:new', data)


def publish_comment(data):
    publish('report:comment:new', data)


def publish_mention(data):
    publish('mention:new', data)


def publish_report_image(data):
    publish('report:image:new', data)


def publish_report_flag(data):
    publish('report:flag:new', data)


def publish_report_state(data):
    publish('report:state:new', data)
