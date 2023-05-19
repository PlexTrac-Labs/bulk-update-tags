import yaml
from tabulate import tabulate
from copy import deepcopy
import requests

import settings
import utils.log_handler as logger
log = logger.log
from utils.auth_handler import Auth
import utils.input_utils as input
import utils.general_utils as utils
from utils.log_handler import IterationMetrics
import api
from api.exceptions import *


class TagLocations():
    clients = False
    reports = False
    findings = False
    assets = False # client assets
    writeups = False # writeupDB writeups
    # narratives = False # narrativeDB sections
    # rb_procedures = False # runbookDB procedures
    # rb_tactics = False # runbookDB tactics
    # rb_techniques = False # runbookDB techniques
    # rb_methodologies = False # runbookDB methodologies
    # rb_engagements = False # runbook engagements
    # priorities = False
    # questions = False # assessment questionnaire questions
    # analytics_filers = False # analytic preset filters have tags in them. not sure if this needs to be handled

    def __init__(self):
        self.objs = [attr for attr in TagLocations.__dict__ if ('__' not in attr) & (not callable(getattr(TagLocations, attr)))]        
        
    def display_option_values(self):
        print(tabulate([[self.clients, self.reports, self.findings, self.assets, self.writeups]], headers=self.objs))

    def set_all(self, val: bool):
        for obj in self.objs:
            self.__setattr__(obj, val)

    def get_selected(self) -> list:
        selected = []
        for obj in self.objs:
            if self.__getattribute__(obj):
                selected.append(obj)
        return selected

    def is_all_selected(self) -> bool:
        is_all_selected = True
        for obj in self.objs:
            if not self.__getattribute__(obj):
                is_all_selected = False
        return is_all_selected



def get_tag_locations_from_user(tl: TagLocations) -> TagLocations:
    log.info(f'Tags can be stored on the following objects in a Plextrac instance: {tl.objs}')
    while True:
        choice = input.user_options(f'Select objects to update tags on. Enter a selected object to deselect. Enter done to continue', "Invalid option", tl.objs + ["done"])
        if choice == "done":
            break
        update = not tl.__getattribute__(choice)
        tl.__setattr__(choice, update)
        log.info(f'{"Selected" if update else "Deselected"} {choice}')
        log.info(f'Currently selected locations to update tags')
        tl.display_option_values()

    return tl


def get_multiple_tags_from_user(tags: list, sanitize:bool=True) -> None:
    if len(tags) > 0:
        if input.user_options(f'Would you like to add another tag?', f'Invalid option', ["y", "n"]) != "y":
            return None
        
    tag = get_tag_from_user(sanitize=sanitize)
    tags.append(tag)

    get_multiple_tags_from_user(tags)
    return None


def get_tag_from_user(msg:str="Please enter a tag", sanitize:bool=True) -> str:
    tag = input.prompt_user(msg)
    
    if sanitize == False:
        return tag
    
    clean_tag = utils.format_key(tag)
    if tag == clean_tag:
        return tag
    
    if input.continue_anyways(f'You might have enter an invalid tag string. \'{tag}\' is ideally formatted \'{clean_tag}\''):
        return tag
    else:
        return get_tag_from_user()
        

def get_page_of_clients(page: int = 0, clients: list = [], total_clients: int = -1) -> None:
    """
    Handles traversing pagination results to create a list of all items.

    :param page: page to start on, for all results use 0, defaults to 0
    :type page: int, optional
    :param clients: the list passed in will be added to, acts as return, defaults to []
    :type clients: list, optional
    :param total_clients: used for recursion to know when all pages have been gathered, defaults to -1
    :type total_clients: int, optional
    """
    payload = {
        "pagination": {
            "offset": page*100,
            "limit": 100
        }
    }
    # client data from response is shaped like
    # {
    #     "client_id": 4155,
    #     "name": "Test Client",
    #     "poc": "poc name",
    #     "tags": [
    #         "test"
    #     ]
    # }
    response = api._v2.clients.list_clients(auth.base_url, auth.get_auth_headers(), payload)
    if response.json['status'] != "success":
        log.critical(f'Could not retrieve clients from instance. Exiting...')
        exit()
    if len(response.json['data']) > 0:
        clients += deepcopy(response.json['data'])
        total_clients = response.json['meta']['pagination']['total']

    if len(clients) != total_clients:
        return get_page_of_clients(page+1, clients, total_clients)
    
    return None


def get_page_of_assets(page: int = 0, assets: list = [], total_assets: int = -1) -> None:
    """
    Handles traversing pagination results to create a list of all items.

    :param page: page to start on, for all results use 0, defaults to 0
    :type page: int, optional
    :param assets: the list passed in will be added to, acts as return, defaults to []
    :type assets: list, optional
    :param total_assets: used for recursion to know when all pages have been gathered, defaults to -1
    :type total_assets: int, optional
    """
    payload = {
        "pagination": {
            "offset": page*1000,
            "limit": 1000
        }
    }
    # asset data from response is shaped like
    # {
        # "asset": "testing asset",
        # "assetCriticality": "High",
        # "child_assets": {},
        # "client_id": 1618,
        # "created": "2022-05-12T13:44:51.087Z",
        # "createdAt": 1652363091087,
        # "doc_type": "client_asset",
        # "findings": {},
        # "id": "62f14f93-52f0-4fc5-86de-fff2c7fe397c",
        # "knownIps": [],
        # "parent_asset": null,
        # "updatedAt": 1652363091087
    # }
    response = api._v2.assets.get_tenant_assets(auth.base_url, auth.get_auth_headers(), payload)
    if response.json['status'] != "success":
        log.critical(f'Could not retrieve assets from instance. Exiting...')
        exit()
    if len(response.json['assets']) > 0:
        assets += deepcopy(response.json['assets'])
        total_assets = response.json['meta']['pagination']['total']

    if len(assets) != total_assets:
        return get_page_of_assets(page+1, assets, total_assets)
    
    return None


def get_page_of_reports(page: int, reports: list = [], total_reports: int = -1) -> None:
    """
    Handles traversing pagination results to create a list of all items.

    :param page: page to start on, for all results use 0, defaults to 0
    :type page: int, optional
    :param reports: the list passed in will be added to, acts as return, defaults to []
    :type reports: list, optional
    :param total_reports: used for recursion to know when all pages have been gathered, defaults to -1
    :type total_reports: int, optional
    """
    payload = {
        "pagination": {
            "offset": page*1000,
            "limit": 1000
        }
    }
    # report data from response is shaped like
    # {
        # "client_id": 4155,
        # "id": 500004,
        # "name": "test",
        # "status": "Draft",
        # "findings": 1
    # }
    response = api._v2.reports.get_report_list(auth.base_url, auth.get_auth_headers(), payload)
    if response.json['status'] != "success":
        log.critical(f'Could not retrieve reports from instance. Exiting...')
        exit()
    if len(response.json['data']) > 0:
        reports += deepcopy(response.json['data'])
        total_reports = response.json['meta']['pagination']['total']

    if len(reports) != total_reports:
        return get_page_of_reports(page+1, reports, total_reports)
    
    return None


def get_page_of_findings(client_id: int, report_id: int, page: int = 0, findings: list = [], total_findings: int = -1) -> bool:
    """
    Handles traversing pagination results to create a list of all items.

    :param client_id: id of client
    :type client_id: int
    :param report_id: id of report
    :type report_id: int
    :param page: page to start on, for all results use 0, defaults to 0
    :type page: int, optional
    :param findings: the list passed in will be added to, acts as return, defaults to []
    :type findings: list, optional
    :param total_findings: used for recursion to know when all pages have been gathered, defaults to -1
    :type total_findings: int, optional
    :return: boolean if all page requests were successful
    :rtype: bool
    """
    payload = {
        "pagination": {
            "offset": page*100,
            "limit": 100
        }
    }
    # finding data from response is shaped like
    # {
    #   "affected_assets": {},
    #   "assignedTo": null,
    #   "client_id": 4155,
    #   "createdAt": 1653496110726,
    #   "description": "<p>desc</p>",
    #   "fields": {
    #     "field1": {
    #       "label": "Label",
    #       "value": "<p>value</p>"
    #     }
    #   },
    #   "flaw_id": 3929198681,
    #   "jiraIssueKey": null,
    #   "jiraIssueLink": null,
    #   "last_update": 1653496244421,
    #   "report_id": 500006,
    #   "serviceNowTicketKey": null,
    #   "serviceNowTicketTable": null,
    #   "severity": "Critical",
    #   "status": "Open",
    #   "tags": [
    #     "test_tag"
    #   ],
    #   "title": "Finding Changed",
    #   "visibility": "draft",
    #   "timeToNearestSLA": ""
    # }
    response = api._v2.findings.get_findings_by_report(auth.base_url, auth.get_auth_headers(), client_id, report_id, payload)
    if response.json['status'] != "success":
        log.exception(f'Could not retrieve findings from report. Skipping...')
        return False
    if len(response.json['data']) > 0:
        findings += deepcopy(response.json['data'])
        total_findings = response.json['meta']['pagination']['total']

    if len(findings) != total_findings:
        return get_page_of_findings(client_id, report_id, page+1, findings, total_findings)
    
    return True


def get_writeups(writeups: list = []) -> None:
    """
    Gets a list of all writeups from tenant

    :param writeups: the list passed in will be added to, acts as return, defaults to []
    :type writeups: list, optional
    :raises Exception: _description_
    """
    # writeup data from response is shaped like
    # {
        # "description": "Sample description",
        # "doc_id": 225828,
        # "doc_type": "template",
        # "fields": {
            # "field_one_key": {
                # "label": "Field One",
                # "value": "1111111"
            # }
        # },
        # "recommendations": "Sample recommendations",
        # "references": "Sample references",
        # "repositoryId": "cl33cyus...",
        # "severity": "Informational",
        # "source": "Custom",
        # "tags": [
            # "test"
        # ],
        # "tenantId": 0,
        # "title": "Sample Writeup"
    # }
    try:
        response = api._v1._content_library.writeups.list_writeups(auth.base_url, auth.get_auth_headers())
    except Exception as e:
        raise Exception(f'Could not retrieve writeups from instance.') from e
    writeups += deepcopy(response.json)


def add_tags_to_tenant(tags: list) -> bool:
    """
    _summary_

    :param tags: _description_
    :type tags: list
    :return: _description_
    :rtype: bool
    """
    log.info(f'Adding new tags to tenant...')
    all_added_successfully = True
    for tag in tags:
        try:
            payload = {
                "name": tag,
                "scope": "tenant",
                "ownerId": auth.tenant_id
            }
            api._v1._tenant.tags.create_tenant_tag(auth.base_url, auth.get_auth_headers(), auth.tenant_id, payload)
        except PTWrapperLibraryFailed as e:
            if e.response.status_code == 409:
                log.info(f'Tag already exists at tenant level.')
            else:
                log.exception(f'Could not create tenant tag \'{tag}\'. This tag will not appear in tag dropdowns. Skipping...')
                all_added_successfully = False
    return all_added_successfully


def remove_tags_from_tenant(tags: list) -> bool:
    """
    _summary_

    :param tags: _description_
    :type tags: list
    :return: _description_
    :rtype: bool
    """
    log.info(f'Removing tags from tenant level...')
    all_removed_successfully = True
    for tag in tags:
        try:
            response = api._v1._tenant.tags.delete_tenant_tag(auth.base_url, auth.get_auth_headers(), auth.tenant_id, f'tag_tenant_{auth.tenant_id}_{tag}')
            log.success(f'Removed \'{tag}\' from tenant')
        except PTWrapperLibraryFailed as e:
            if e.response.status_code == 404:
                log.info(f'Tag already removed at tenant level.')
            else:
                log.exception(f'Could not delete tenant tag \'{tag}\'. Skipping...')
                all_removed_successfully = False
    return all_removed_successfully


# def handle_remove_tags():
#     tl = get_tag_locations_from_user(TagLocations())
#     tags = []
#     get_multiple_tags_from_user(tags, sanitize=False)
#     log.info(f'Selected tags to remove: {tags}')
#     log.info(f'Loading {tl.get_selected()} from instance...')
#     # loaded this many are you sure you want to remove
#     is_all_removed_successfully = True
#     # remove all
#     if tl.is_all_selected and is_all_removed_successfully:
#         remove_tags_from_tenant(tags)


def handle_refractor_tags():
    tl = TagLocations()
    tl.set_all(True)

    # get tag replacements from user
    # ------------------------------
    log.info(f'Since this operation affects many objects in the Plextrac DB it is better to make all tag refractions at once.')
    log.info(f'First enter each tag that needs to be refractored. Afterwards you will enter the replacement for each entered tag.')
    tags = []
    replacements = []
    to_string_repacements = ""
    get_multiple_tags_from_user(tags)
    for tag in tags:
        replacement = get_tag_from_user(f'Enter a replacement tag for {tag}')
        replacements.append(replacement)
        to_string_repacements += f"'{tag}' -> '{replacement}' | "
    to_string_repacements = to_string_repacements[:-3]

    log.info(f'Selected following refractions: {to_string_repacements}')
    if not input.continue_prompt("Make selected refractions"):
        exit()

    # load objects from PT
    # --------------------
    log.info(f'Loading objects from from Plextrac instance...')

    # get list of all clients in instance
    clients = []
    get_page_of_clients(0, clients=clients)
    log.debug(f'num of clients founds: {len(clients)}')

    # get list of all assets in instance
    assets = []
    get_page_of_assets(0, assets=assets)
    log.debug(f'num of assets founds: {len(assets)}')

    # get list of all report in instance - findings will be later called from reports
    reports = []
    get_page_of_reports(0, reports=reports)
    log.debug(f'num of reports founds: {len(reports)}')

    # get list of all writeups in instance
    writeups = []
    get_writeups(writeups)
    log.debug(f'num of writeups founds: {len(writeups)}')

    # refractor tags
    # --------------
    log.info(f'Loaded {len(clients)} client(s), {len(assets)} asset(s), {len(reports)} report(s), and {len(writeups)} writeup(s) from your Plextrac instance.')
    if not input.continue_prompt(f'This will make requests to all objects that need to be refractored. This make take awhile'):
        exit()

    is_all_removed_successfully = True
    skipped_objects = [0,0,0,0,0] # count of client, asset, report, finding, writeups that could not be refractored

     # add new tags to tenant
    # ----------------------
    add_tags_to_tenant(replacements)
        
    # refractor client tags
    metrics = IterationMetrics(len(clients))
    for client in clients:
        log.info(f'Processing tags in client \'{client["name"]}\'...')

        # check if the client tags need to be update, the check here saves an api call if not required
        if len(client.get('tags', [])) < 1:
            log.info(f'Contains no tags')
            log.info(metrics.print_iter_metrics())
            continue
        needs_update = False
        for tag in tags:
            if tag in client.get('tags', []):
                needs_update = True
        if not needs_update:
            log.info(f'Contains no tags to refractor')
            log.info(metrics.print_iter_metrics())
            continue

        # get full client object
        try:
            response = api._v1.clients.get_client(auth.base_url, auth.get_auth_headers(), client['client_id'])
        except Exception as e:
            log.exception(f'Could not load client. Skipping...')
            is_all_removed_successfully = False
            skipped_objects[0] += 1
            log.info(metrics.print_iter_metrics())
            continue
        client_tag_update_payload = {"tags": response.json.get('tags', [])}

        # refractor tags on client
        for i, tag in enumerate(client_tag_update_payload['tags']): # checking each client tag to see if it needs to be replaced
            if tag in tags:
                j = tags.index(tag)
                client_tag_update_payload['tags'].pop(i)
                client_tag_update_payload['tags'].insert(i, replacements[j])

        # update client
        try:
            response = api._v1.clients.update_client(auth.base_url, auth.get_auth_headers(), client['client_id'], client_tag_update_payload)
        except Exception as e:
            log.exception(f'Could not update client. Skipping...')
            is_all_removed_successfully = False
            skipped_objects[0] += 1
            log.info(metrics.print_iter_metrics())
            continue

        log.success(f'Refractored all tags in {client["name"]}')
        log.info(metrics.print_iter_metrics())

    # refractor asset tags
    metrics = IterationMetrics(len(assets))
    for asset in assets:
        log.info(f'Processing tags in asset \'{asset["asset"]}\'...')

        # check if the asset tags need to be update, the check here saves an api call if not required
        if len(asset.get('tags', [])) < 1:
            log.info(f'Contains no tags')
            log.info(metrics.print_iter_metrics())
            continue
        needs_update = False
        for tag in tags:
            if tag in asset.get('tags', []):
                needs_update = True
        if not needs_update:
            log.info(f'Contains no tags to refractor')
            log.info(metrics.print_iter_metrics())
            continue

        # get full asset object
        try:
            response = api._v1.assets.get_asset(auth.base_url, auth.get_auth_headers(), asset['client_id'], asset['id'])
        except Exception as e:
            log.exception(f'Could not load asset. Skipping...')
            is_all_removed_successfully = False
            skipped_objects[1] += 1
            log.info(metrics.print_iter_metrics())
            continue
        detailed_asset = response.json

        # refractor tags on asset
        for i, tag in enumerate(detailed_asset.get("tags", [])): # checking each asset tag to see if it needs to be replaced
            if tag in tags:
                j = tags.index(tag)
                detailed_asset['tags'].pop(i)
                detailed_asset['tags'].insert(i, replacements[j])

        # update asset
        try:
            response = api._v1.assets.update_asset(auth.base_url, auth.get_auth_headers(), asset['client_id'], asset['id'], detailed_asset)
        except Exception as e:
            log.exception(f'Could not update asset. Skipping...')
            is_all_removed_successfully = False
            skipped_objects[1] += 1
            log.info(metrics.print_iter_metrics())
            continue

        log.success(f'Refractored all tags in {asset["asset"]}')
        log.info(metrics.print_iter_metrics())

    # refractor report tags
    metrics = IterationMetrics(len(reports))
    for report in reports:
        log.info(f'Processing tags in report \'{report["name"]}\'...')

        # check if the report tags need to be update, the check here saves an api call if not required
        report_needs_update = False
        for tag in tags:
            if tag in report.get('tags', []):
                report_needs_update = True
        if report_needs_update:
            # get full report object
            try:
                response = api._v1.reports.get_report(auth.base_url, auth.get_auth_headers(), report['client_id'], report['id'])
            except Exception as e:
                log.exception(f'Could not load report. Skipping...')
                is_all_removed_successfully = False
                skipped_objects[2] += 1
                log.info(metrics.print_iter_metrics())
                continue
            detailed_report = response.json

            # refractor tags on report
            for i, tag in enumerate(detailed_report.get("tags", [])): # checking each report tag to see if it needs to be replaced
                if tag in tags:
                    j = tags.index(tag)
                    detailed_report['tags'].pop(i)
                    detailed_report['tags'].insert(i, replacements[j])

            # update report
            try:
                response = api._v1.reports.update_report(auth.base_url, auth.get_auth_headers(), report['client_id'], report['id'], detailed_report)
            except Exception as e:
                log.exception(f'Could not update report. Skipping...')
                is_all_removed_successfully = False
                skipped_objects[2] += 1
                log.info(metrics.print_iter_metrics())
                continue

            log.success(f'Refractored all tags in {report["name"]}')
        else:
            log.info(f'Report contains no tags to refractor')

        # refractor finding tags
        if report.get('findings', 0) < 1:
            continue
        log.info(f'Loading findings from report...')
        findings = []
        if not get_page_of_findings(report['client_id'], report['id'], 0, findings=findings):
            continue
        log.debug(f'num of findings founds: {len(findings)}')

        findings_metrics = IterationMetrics(len(findings))
        for finding in findings:
            log.info(f'Processing tags in finding \'{finding["title"]}\'...')

            # check if the finding tags need to be update, the check here saves an api call if not required
            if len(finding.get('tags', [])) < 1:
                log.info(f'Contains no tags')
                log.info(findings_metrics.print_iter_metrics())
                continue
            needs_update = False
            for tag in tags:
                if tag in finding.get('tags', []):
                    needs_update = True
            if not needs_update:
                log.info(f'Contains no tags to refractor')
                log.info(findings_metrics.print_iter_metrics())
                continue

            # refractor tags on finding
            for i, tag in enumerate(finding.get("tags", [])): # checking each finding tag to see if it needs to be replaced
                if tag in tags:
                    j = tags.index(tag)
                    finding['tags'].pop(i)
                    finding['tags'].insert(i, replacements[j])

            # update finding
            try:
                response = api._v1.findings.update_finding(auth.base_url, auth.get_auth_headers(), finding['client_id'], finding['report_id'], finding['flaw_id'], finding)
            except Exception as e:
                log.exception(f'Could not update finding. Skipping...')
                is_all_removed_successfully = False
                skipped_objects[3] += 1
                log.info(findings_metrics.print_iter_metrics())
                continue

            log.success(f'Refractored all tags in {finding["title"]}')
            log.info(findings_metrics.print_iter_metrics())

        # metrics for report tags and findings on report
        log.info(metrics.print_iter_metrics())

    # refractor writeup tags
    metrics = IterationMetrics(len(writeups))
    for writeup in writeups:
        log.info(f'Processing tags in writeup \'{writeup["title"]}\'...')

        # refractor tags on writeup
        needs_update = False
        for i, tag in enumerate(writeup.get("tags", [])): # checking each writeup tag to see if it needs to be replaced
            if tag in tags:
                j = tags.index(tag)
                writeup['tags'].pop(i)
                writeup['tags'].insert(i, replacements[j])
                needs_update = True

        # check if the writeup tags need to be update, the check here saves an api call if not required
        if not needs_update:
            log.info(f'Contains no tags to refractor')
            log.info(metrics.print_iter_metrics())
            continue

        # update writeup
        try:
            response = api._v1._content_library.writeups.update_writeups(auth.base_url, auth.get_auth_headers(), writeup['doc_id'], writeup)
        except Exception as e:
            log.exception(f'Could not update writeup. Skipping...')
            is_all_removed_successfully = False
            skipped_objects[4] += 1
            log.info(metrics.print_iter_metrics())
            continue

        log.success(f'Refractored all tags in {writeup["title"]}')
        log.info(metrics.print_iter_metrics())

    log.info(f'\n\nFinished refractoring tags on objects.\n')
    if not is_all_removed_successfully:
        log.info(f'Could not refractor {skipped_objects[0]} client(s), {skipped_objects[1]} asset(s), {skipped_objects[2]} report(s), {skipped_objects[3]} finding(s), and {skipped_objects[4]} writeup(s). See log file for details')
        log.info(f'Skipping removing tag from tenant since all references of tags were not removed from objects')
        log.info(f'Completed. See log file for details')
        exit()

    # remove tags from tenant
    # ----------------------
    remove_tags_from_tenant(tags)

    log.info(f'Completed. See log file for details')



if __name__ == '__main__':
    for i in settings.script_info:
        print(i)

    with open("config.yaml", 'r') as f:
        args = yaml.safe_load(f)

    auth = Auth(args)
    auth.handle_authentication()

    # VALID_TAG_ACTIONS = ["remove", "refractor"]
    # tag_action = input.user_options(f'Select whether you want to remove or refractor tags', "Invalid option", VALID_TAG_ACTIONS)
    # if tag_action == "remove":
    #     handle_remove_tags()
    # elif tag_action == "refractor":
    #     handle_refractor_tags()

    handle_refractor_tags()
