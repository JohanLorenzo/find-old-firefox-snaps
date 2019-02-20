#!/usr/bin/env python

import json

from os import listdir
from os.path import isfile, join

from taskcluster import Queue
from taskcluster.exceptions import TaskclusterRestFailure
from taskhuddler import TaskGraph
from taskhuddler.utils import tc_options

queue = Queue(options=tc_options())

KNOWN_VERSIONS_AND_BUILDS = (
    ('59.0b12', 1),
    ('59.0b14', 1),
    ('59.0rc', 1),
    ('59.0rc', 4),
    ('59.0rc', 5),
    ('59.0.1', 1),
    ('59.0.2', 1),
    ('59.0.3', 1),
    ('59.0b13', 1),
    ('60.0.1', 1),
    ('60.0.1', 2),
    ('60.0.1esr', 1),
    ('60.0.2', 1),
    ('60.0.2esr', 1),
    ('60.0.2esr', 2),
    ('60.0', 1),
    ('60.0', 2),
    ('60.0b10', 1),
    ('60.0b11', 1),
    ('60.0b11', 2,),
    ('60.0b12', 1,),
    ('60.0b13', 1),
    ('60.0b14', 2,),
    ('60.0b15', 1),
    ('60.0b16', 1),
    ('60.0b3', 1),
    ('60.0b4', 1),
    ('60.0b5', 1),
    ('60.0b6', 1),
    ('60.0b7', 1),
    ('60.0b8', 1,),
    ('60.0b9', 1),
    ('60.0esr', 3),
    ('60.0esr', 5),
    ('60.0esr', 6),
    ('60.1.0esr', 1),
    ('60.1.0esr', 2),
    ('60.2.0esr', 1),
    ('60.2.0esr', 2),
    ('60.2.1esr', 1),
    ('60.2.2esr', 1),
    ('60.3.0esr', 2),
    ('60.4.0esr', 2),
    ('61.0.1', 1),
    ('61.0.2', 1),
    ('61.0', 1),
    ('61.0', 2),
    ('61.0', 3),
    ('61.0b10', 1),
    ('61.0b11', 1),
    ('61.0b12', 1,),
    ('61.0b13', 1),
    ('61.0b14', 1),
    ('61.0b3', 1),
    ('61.0b4', 1),
    ('61.0b5', 1),
    ('61.0b6', 1),
    ('61.0b7', 1),
    ('61.0b8', 1),
    ('61.0b9', 1),
    ('62.0.2', 1),
    ('62.0.3', 1),
    ('62.0', 1),
    ('62.0', 2),
    ('62.0b10', 1),
    ('62.0b11', 1),
    ('62.0b12', 1),
    ('62.0b13', 1),
    ('62.0b14', 1),
    ('62.0b15', 2),
    ('62.0b16', 1),
    ('62.0b17', 1),
    ('62.0b18', 1,),
    ('62.0b19', 1),
    ('62.0b20', 1),
    ('62.0b3', 1),
    ('62.0b4', 1),
    ('62.0b5', 1),
    ('62.0b6', 1),
    ('62.0b7', 1,),
    ('62.0b8', 1),
    ('62.0b9', 1),
    ('63.0.1', 4),
    ('63.0.3', 1),
    ('63.0b10', 1),
    ('63.0b11', 1),
    ('63.0b12', 1),
    ('63.0b12', 2),
    ('63.0b13', 1),
    ('63.0b14', 1),
    ('63.0b3', 1),
    ('63.0b4', 1),
    ('63.0b5', 1),
    ('63.0b6', 1),
    ('63.0b7', 1),
    ('63.0b8', 1),
    ('63.0b9', 1,),
    ('63.0rc', 1),
    ('63.0rc', 2),
    ('64.0', 1),
    ('64.0', 2),
    ('64.0', 3),
    ('64.0b10', 1),
    ('64.0b11', 1),
    ('64.0b12', 1),
    ('64.0b13', 1),
    ('64.0b14', 1),
    ('64.0b3', 1),
    ('64.0b4', 1),
    ('64.0b4', 2),
    ('64.0b5', 1),
    ('64.0b6', 1),
    ('64.0b7', 1),
    ('64.0b8', 1),
    ('64.0b9', 1),
    ('65.0b3', 1),
    ('65.0b4', 1),
)


def get_json_files_paths():
    json_folder = '/home/jlorenzo/git/mozilla-releng/releasewarrior-data/archive/firefox'
    only_files = (
        join(json_folder, f) for f in listdir(json_folder) if isfile(join(json_folder, f))
    )
    only_json = (f for f in only_files if f.endswith('.json'))
    only_old_enough_version = (f for f in only_json if '-59' in f)
    return only_old_enough_version


def get_promote_graph_ids(json_path):
    with open(json_path) as f:
        json_data = json.load(f)

    version = json_data['version']

    for release in json_data['inflight']:
        build_number = release['buildnum']
        graphids = release['graphids']
        if len(graphids) > 0:

            # import pdb; pdb.set_trace()

            if isinstance(graphids[0], list):
                promote_graph_ids = [
                    promote_graph_id
                    for graph_type, promote_graph_id in graphids
                    if graph_type in ('promote', 'promote_rc')
                ]
            else:
                promote_graph_ids = [graphids[0]]
            if len(promote_graph_ids) != 1:
                raise Exception('version "{}" build {} does not have a singular promote graph: {}'.format(version, build_number, graphids))

            yield promote_graph_ids[0], version, build_number


def get_snap_task_id(promote_graph_id):
    graph = TaskGraph(promote_graph_id)

    snap_tasks = [task for task in graph.tasks() if '-snap-' in task.name and task.completed]

    if len(snap_tasks) != 1:
        task_ids = [task.taskid for task in snap_tasks]
        if 'QSnfB6LMS--TgiQM9nNAKw' in task_ids:
            snap_tasks = [
                task for task in snap_tasks
                if task.taskid == 'QSnfB6LMS--TgiQM9nNAKw'
            ]
        else:
            raise Exception('Graph "{}" does not have a unique task: {}'.format(promote_graph_id, task_ids))

    task = snap_tasks[0]
    return task.taskid, task.completed


def get_artifacts_urls(snap_task_id):
    artifacts_data = queue.listLatestArtifacts(snap_task_id)
    artifacts_paths = [
        artifact['name']
        for artifact in artifacts_data['artifacts']
        if '.snap' in artifact['name']
    ]
    if len(artifacts_paths) != 2:
        raise Exception('"{}" does not have 2 artifacts: {}'.format(snap_task_id, artifacts_paths))
    for path in artifacts_paths:
        yield 'https://queue.taskcluster.net/v1/task/{}/artifacts/{}'.format(snap_task_id, path)

for json_path in get_json_files_paths():
    for promote_graph_id, version, build_number in get_promote_graph_ids(json_path):
        if (version, build_number) in KNOWN_VERSIONS_AND_BUILDS:
            print('Skipping {} build {}'.format(version, build_number))
            continue

        try:
            promote_task = queue.status(promote_graph_id)
            if promote_task['status']['state'] != 'completed':
                continue
        except TaskclusterRestFailure as e:
            if e.status_code == 404:
                print('Skipping {} build {} because promote task does not exist anymore'.format(version, build_number))
                continue
            else:
                raise

        snap_task_id, is_completed = get_snap_task_id(promote_graph_id)

        if not is_completed:
            continue

        for artifact_url in get_artifacts_urls(snap_task_id):
            is_checksum = artifact_url.endswith('.checksums')
            destination_url = 'https://archive.mozilla.org/pub/firefox/candidates/{version}-candidates/build{build_number}/snap/firefox-{version}.snap{postfix}'.format(
                version=version[:-len('rc')] if version.endswith('rc') else version,
                build_number=build_number,
                postfix='.checksums' if is_checksum else ''
            )
            print(destination_url, artifact_url)
