#!/usr/bin/env python
from migrate.versioning.shell import main
main(url='sqlite:///payment.db', debug='False', repository='migration/')
