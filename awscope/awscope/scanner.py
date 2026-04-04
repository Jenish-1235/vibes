from __future__ import annotations

import logging
from typing import Callable

import boto3
from botocore.exceptions import ClientError

from awscope.models import AwsResource

log = logging.getLogger(__name__)

# ── helpers ────────────────────────────────────────────────────────────────

def _tags(raw_tags: list[dict] | None) -> dict[str, str]:
    if not raw_tags:
        return {}
    return {t["Key"]: t["Value"] for t in raw_tags}


def _name(tags: dict[str, str], fallback: str) -> str:
    return tags.get("Name") or tags.get("name") or fallback


def _safe(fn: Callable, account_alias: str, region: str, service: str) -> list[AwsResource]:
    try:
        return fn()
    except ClientError as e:
        code = e.response["Error"]["Code"]
        log.warning("[%s/%s/%s] %s — skipping", account_alias, region, service, code)
        return []
    except Exception as e:
        log.warning("[%s/%s/%s] %s — skipping", account_alias, region, service, e)
        return []


# ── per-service collectors ─────────────────────────────────────────────────

def collect_ec2_instances(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_instances")
        resources = []
        for page in paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["running"]}]):
            for reservation in page["Reservations"]:
                for inst in reservation["Instances"]:
                    tags = _tags(inst.get("Tags"))
                    resources.append(AwsResource(
                        resource_id=inst["InstanceId"],
                        name=_name(tags, inst["InstanceId"]),
                        resource_type="ec2:instance",
                        arn=f"arn:aws:ec2:{region}:{account_id}:instance/{inst['InstanceId']}",
                        region=region, account_alias=account_alias, account_id=account_id,
                        status=inst["State"]["Name"],
                        tags=tags, raw=inst,
                    ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:instance")


def collect_s3_buckets(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("s3", region_name="us-east-1")
        buckets = client.list_buckets().get("Buckets", [])
        resources = []
        for b in buckets:
            name = b["Name"]
            try:
                tag_resp = client.get_bucket_tagging(Bucket=name)
                tags = _tags(tag_resp.get("TagSet"))
            except ClientError:
                tags = {}
            resources.append(AwsResource(
                resource_id=name, name=name, resource_type="s3:bucket",
                arn=f"arn:aws:s3:::{name}", region="global",
                account_alias=account_alias, account_id=account_id,
                status="active", tags=tags, raw=b,
            ))
        return resources
    return _safe(_collect, account_alias, "global", "s3:bucket")


def collect_rds_instances(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("rds", region_name=region)
        paginator = client.get_paginator("describe_db_instances")
        resources = []
        for page in paginator.paginate():
            for db in page["DBInstances"]:
                if db["DBInstanceStatus"] != "available":
                    continue
                tags = _tags(db.get("TagList"))
                resources.append(AwsResource(
                    resource_id=db["DBInstanceIdentifier"],
                    name=_name(tags, db["DBInstanceIdentifier"]),
                    resource_type="rds:db",
                    arn=db.get("DBInstanceArn", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=db["DBInstanceStatus"], tags=tags, raw=db,
                ))
        return resources
    return _safe(_collect, account_alias, region, "rds:db")


def collect_lambda_functions(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("lambda", region_name=region)
        paginator = client.get_paginator("list_functions")
        resources = []
        for page in paginator.paginate():
            for fn in page["Functions"]:
                arn = fn["FunctionArn"]
                try:
                    tag_resp = client.list_tags(Resource=arn)
                    tags = tag_resp.get("Tags", {})
                except ClientError:
                    tags = {}
                resources.append(AwsResource(
                    resource_id=fn["FunctionName"], name=fn["FunctionName"],
                    resource_type="lambda:function", arn=arn,
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=fn,
                ))
        return resources
    return _safe(_collect, account_alias, region, "lambda:function")


def collect_ecs_clusters(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ecs", region_name=region)
        arns = []
        paginator = client.get_paginator("list_clusters")
        for page in paginator.paginate():
            arns.extend(page["clusterArns"])
        if not arns:
            return []
        clusters = client.describe_clusters(clusters=arns, include=["TAGS"])["clusters"]
        resources = []
        for c in clusters:
            tags = {t["key"]: t["value"] for t in c.get("tags", [])}
            resources.append(AwsResource(
                resource_id=c["clusterName"], name=c["clusterName"],
                resource_type="ecs:cluster", arn=c["clusterArn"],
                region=region, account_alias=account_alias, account_id=account_id,
                status=c["status"].lower(), tags=tags, raw=c,
            ))
        return resources
    return _safe(_collect, account_alias, region, "ecs:cluster")


def collect_eks_clusters(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("eks", region_name=region)
        paginator = client.get_paginator("list_clusters")
        names = []
        for page in paginator.paginate():
            names.extend(page["clusters"])
        resources = []
        for name in names:
            cluster = client.describe_cluster(name=name)["cluster"]
            resources.append(AwsResource(
                resource_id=name, name=name, resource_type="eks:cluster",
                arn=cluster.get("arn", ""),
                region=region, account_alias=account_alias, account_id=account_id,
                status=cluster.get("status", "").lower(),
                tags=cluster.get("tags", {}), raw=cluster,
            ))
        return resources
    return _safe(_collect, account_alias, region, "eks:cluster")


def collect_cloudfront_distributions(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("cloudfront", region_name="us-east-1")
        paginator = client.get_paginator("list_distributions")
        resources = []
        for page in paginator.paginate():
            for dist in page.get("DistributionList", {}).get("Items", []):
                resources.append(AwsResource(
                    resource_id=dist["Id"], name=dist.get("Comment") or dist["Id"],
                    resource_type="cloudfront:distribution", arn=dist["ARN"],
                    region="global", account_alias=account_alias, account_id=account_id,
                    status=dist["Status"].lower(), tags={}, raw=dist,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "cloudfront:distribution")


def collect_dynamodb_tables(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("dynamodb", region_name=region)
        paginator = client.get_paginator("list_tables")
        resources = []
        for page in paginator.paginate():
            for table_name in page["TableNames"]:
                desc = client.describe_table(TableName=table_name)["Table"]
                try:
                    tag_resp = client.list_tags_of_resource(ResourceArn=desc["TableArn"])
                    tags = _tags(tag_resp.get("Tags"))
                except ClientError:
                    tags = {}
                resources.append(AwsResource(
                    resource_id=table_name, name=table_name,
                    resource_type="dynamodb:table",
                    arn=desc.get("TableArn", f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=desc["TableStatus"].lower(), tags=tags, raw=desc,
                ))
        return resources
    return _safe(_collect, account_alias, region, "dynamodb:table")


def collect_sqs_queues(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("sqs", region_name=region)
        paginator = client.get_paginator("list_queues")
        resources = []
        for page in paginator.paginate():
            for url in page.get("QueueUrls", []):
                queue_name = url.split("/")[-1]
                try:
                    tag_resp = client.list_queue_tags(QueueUrl=url)
                    tags = tag_resp.get("Tags", {})
                except ClientError:
                    tags = {}
                resources.append(AwsResource(
                    resource_id=queue_name, name=queue_name,
                    resource_type="sqs:queue", arn=url,
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw={"QueueUrl": url},
                ))
        return resources
    return _safe(_collect, account_alias, region, "sqs:queue")


def collect_sns_topics(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("sns", region_name=region)
        paginator = client.get_paginator("list_topics")
        resources = []
        for page in paginator.paginate():
            for topic in page["Topics"]:
                arn = topic["TopicArn"]
                topic_name = arn.split(":")[-1]
                try:
                    tag_resp = client.list_tags_for_resource(ResourceArn=arn)
                    tags = {t["Key"]: t["Value"] for t in tag_resp.get("Tags", [])}
                except ClientError:
                    tags = {}
                resources.append(AwsResource(
                    resource_id=topic_name, name=topic_name,
                    resource_type="sns:topic", arn=arn,
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=topic,
                ))
        return resources
    return _safe(_collect, account_alias, region, "sns:topic")


def collect_elasticache_clusters(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("elasticache", region_name=region)
        paginator = client.get_paginator("describe_cache_clusters")
        resources = []
        for page in paginator.paginate():
            for c in page["CacheClusters"]:
                resources.append(AwsResource(
                    resource_id=c["CacheClusterId"], name=c["CacheClusterId"],
                    resource_type="elasticache:cluster",
                    arn=c.get("ARN", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=c["CacheClusterStatus"], tags={}, raw=c,
                ))
        return resources
    return _safe(_collect, account_alias, region, "elasticache:cluster")


def collect_elasticache_replication_groups(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("elasticache", region_name=region)
        paginator = client.get_paginator("describe_replication_groups")
        resources = []
        for page in paginator.paginate():
            for rg in page["ReplicationGroups"]:
                resources.append(AwsResource(
                    resource_id=rg["ReplicationGroupId"],
                    name=rg.get("Description") or rg["ReplicationGroupId"],
                    resource_type="elasticache:replication-group",
                    arn=rg.get("ARN", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=rg["Status"], tags={}, raw=rg,
                ))
        return resources
    return _safe(_collect, account_alias, region, "elasticache:replication-group")


def collect_route53_hosted_zones(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("route53", region_name="us-east-1")
        paginator = client.get_paginator("list_hosted_zones")
        resources = []
        for page in paginator.paginate():
            for zone in page["HostedZones"]:
                zone_id = zone["Id"].split("/")[-1]
                resources.append(AwsResource(
                    resource_id=zone_id, name=zone["Name"].rstrip("."),
                    resource_type="route53:hosted-zone",
                    arn=f"arn:aws:route53:::hostedzone/{zone_id}",
                    region="global", account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=zone,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "route53:hosted-zone")


def collect_apigateway_rest_apis(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("apigateway", region_name=region)
        paginator = client.get_paginator("get_rest_apis")
        resources = []
        for page in paginator.paginate():
            for api in page["items"]:
                resources.append(AwsResource(
                    resource_id=api["id"], name=api["name"],
                    resource_type="apigateway:rest-api",
                    arn=f"arn:aws:apigateway:{region}::/restapis/{api['id']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=api.get("tags", {}), raw=api,
                ))
        return resources
    return _safe(_collect, account_alias, region, "apigateway:rest-api")


def collect_apigatewayv2_http_apis(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("apigatewayv2", region_name=region)
        paginator = client.get_paginator("get_apis")
        resources = []
        for page in paginator.paginate():
            for api in page["Items"]:
                resources.append(AwsResource(
                    resource_id=api["ApiId"], name=api["Name"],
                    resource_type="apigateway:http-api",
                    arn=f"arn:aws:apigateway:{region}::/apis/{api['ApiId']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=api.get("Tags", {}), raw=api,
                ))
        return resources
    return _safe(_collect, account_alias, region, "apigateway:http-api")


def collect_secretsmanager_secrets(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("secretsmanager", region_name=region)
        paginator = client.get_paginator("list_secrets")
        resources = []
        for page in paginator.paginate():
            for s in page["SecretList"]:
                tags = _tags(s.get("Tags"))
                resources.append(AwsResource(
                    resource_id=s["Name"], name=s["Name"],
                    resource_type="secretsmanager:secret",
                    arn=s.get("ARN", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=s,
                ))
        return resources
    return _safe(_collect, account_alias, region, "secretsmanager:secret")


def collect_opensearch_domains(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("opensearch", region_name=region)
        names = [d["DomainName"] for d in client.list_domain_names().get("DomainNames", [])]
        if not names:
            return []
        domains = client.describe_domains(DomainNames=names).get("DomainStatusList", [])
        resources = []
        for d in domains:
            resources.append(AwsResource(
                resource_id=d["DomainName"], name=d["DomainName"],
                resource_type="opensearch:domain",
                arn=d.get("ARN", ""),
                region=region, account_alias=account_alias, account_id=account_id,
                status="active" if not d.get("Deleted") else "deleted",
                tags={}, raw=d,
            ))
        return resources
    return _safe(_collect, account_alias, region, "opensearch:domain")


def collect_kinesis_streams(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("kinesis", region_name=region)
        paginator = client.get_paginator("list_streams")
        resources = []
        for page in paginator.paginate():
            for name in page.get("StreamNames", []):
                summary = client.describe_stream_summary(StreamName=name)["StreamDescriptionSummary"]
                resources.append(AwsResource(
                    resource_id=name, name=name,
                    resource_type="kinesis:stream",
                    arn=summary.get("StreamARN", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=summary.get("StreamStatus", "").lower(), tags={}, raw=summary,
                ))
        return resources
    return _safe(_collect, account_alias, region, "kinesis:stream")


def collect_ecr_repositories(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ecr", region_name=region)
        paginator = client.get_paginator("describe_repositories")
        resources = []
        for page in paginator.paginate():
            for repo in page["repositories"]:
                resources.append(AwsResource(
                    resource_id=repo["repositoryName"], name=repo["repositoryName"],
                    resource_type="ecr:repository",
                    arn=repo.get("repositoryArn", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=repo,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ecr:repository")


def collect_redshift_clusters(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("redshift", region_name=region)
        paginator = client.get_paginator("describe_clusters")
        resources = []
        for page in paginator.paginate():
            for c in page["Clusters"]:
                tags = _tags(c.get("Tags"))
                resources.append(AwsResource(
                    resource_id=c["ClusterIdentifier"], name=c["ClusterIdentifier"],
                    resource_type="redshift:cluster",
                    arn=f"arn:aws:redshift:{region}:{account_id}:cluster:{c['ClusterIdentifier']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=c["ClusterStatus"], tags=tags, raw=c,
                ))
        return resources
    return _safe(_collect, account_alias, region, "redshift:cluster")


def collect_autoscaling_groups(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("autoscaling", region_name=region)
        paginator = client.get_paginator("describe_auto_scaling_groups")
        resources = []
        for page in paginator.paginate():
            for asg in page["AutoScalingGroups"]:
                tags = {t["Key"]: t["Value"] for t in asg.get("Tags", [])}
                resources.append(AwsResource(
                    resource_id=asg["AutoScalingGroupName"],
                    name=_name(tags, asg["AutoScalingGroupName"]),
                    resource_type="autoscaling:group",
                    arn=asg.get("AutoScalingGroupARN", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=asg,
                ))
        return resources
    return _safe(_collect, account_alias, region, "autoscaling:group")


# ── IAM collectors (global) ────────────────────────────────────────────────

def collect_iam_users(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("iam", region_name="us-east-1")
        paginator = client.get_paginator("list_users")
        resources = []
        for page in paginator.paginate():
            for user in page["Users"]:
                uname = user["UserName"]
                try:
                    tag_resp = client.list_user_tags(UserName=uname)
                    tags = _tags(tag_resp.get("Tags"))
                except ClientError:
                    tags = {}
                try:
                    mfa = client.list_mfa_devices(UserName=uname)["MFADevices"]
                    mfa_enabled = len(mfa) > 0
                except ClientError:
                    mfa_enabled = False
                try:
                    attached = [p["PolicyName"] for p in
                                client.list_attached_user_policies(UserName=uname)["AttachedPolicies"]]
                except ClientError:
                    attached = []
                try:
                    inline = client.list_user_policies(UserName=uname)["PolicyNames"]
                except ClientError:
                    inline = []
                try:
                    groups = [g["GroupName"] for g in
                              client.list_groups_for_user(UserName=uname)["Groups"]]
                except ClientError:
                    groups = []
                raw = {**user, "mfa_enabled": mfa_enabled,
                       "attached_policies": attached, "inline_policies": inline, "groups": groups}
                resources.append(AwsResource(
                    resource_id=uname, name=uname, resource_type="iam:user",
                    arn=user.get("Arn", ""), region="global",
                    account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=raw,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "iam:user")


def collect_iam_groups(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("iam", region_name="us-east-1")
        paginator = client.get_paginator("list_groups")
        resources = []
        for page in paginator.paginate():
            for group in page["Groups"]:
                gname = group["GroupName"]
                try:
                    members = [u["UserName"] for u in client.get_group(GroupName=gname)["Users"]]
                except ClientError:
                    members = []
                try:
                    attached = [p["PolicyName"] for p in
                                client.list_attached_group_policies(GroupName=gname)["AttachedPolicies"]]
                except ClientError:
                    attached = []
                try:
                    inline = client.list_group_policies(GroupName=gname)["PolicyNames"]
                except ClientError:
                    inline = []
                raw = {**group, "members": members, "attached_policies": attached, "inline_policies": inline}
                resources.append(AwsResource(
                    resource_id=gname, name=gname, resource_type="iam:group",
                    arn=group.get("Arn", ""), region="global",
                    account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=raw,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "iam:group")


def collect_iam_roles(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("iam", region_name="us-east-1")
        paginator = client.get_paginator("list_roles")
        resources = []
        for page in paginator.paginate():
            for role in page["Roles"]:
                # Skip AWS service-linked roles
                if role.get("Path", "").startswith("/aws-service-role/"):
                    continue
                rname = role["RoleName"]
                try:
                    attached = [p["PolicyName"] for p in
                                client.list_attached_role_policies(RoleName=rname)["AttachedPolicies"]]
                except ClientError:
                    attached = []
                try:
                    inline = client.list_role_policies(RoleName=rname)["PolicyNames"]
                except ClientError:
                    inline = []
                raw = {**role, "attached_policies": attached, "inline_policies": inline}
                resources.append(AwsResource(
                    resource_id=rname, name=rname, resource_type="iam:role",
                    arn=role.get("Arn", ""), region="global",
                    account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=raw,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "iam:role")


def collect_iam_customer_policies(session: boto3.Session, account_alias: str, account_id: str) -> list[AwsResource]:
    def _collect():
        client = session.client("iam", region_name="us-east-1")
        paginator = client.get_paginator("list_policies")
        resources = []
        for page in paginator.paginate(Scope="Local"):
            for policy in page["Policies"]:
                resources.append(AwsResource(
                    resource_id=policy["PolicyName"], name=policy["PolicyName"],
                    resource_type="iam:policy",
                    arn=policy.get("Arn", ""), region="global",
                    account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=policy,
                ))
        return resources
    return _safe(_collect, account_alias, "global", "iam:policy")


# ── Networking collectors ──────────────────────────────────────────────────

def collect_vpcs(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        vpcs = client.describe_vpcs()["Vpcs"]
        resources = []
        for vpc in vpcs:
            tags = _tags(vpc.get("Tags"))
            resources.append(AwsResource(
                resource_id=vpc["VpcId"], name=_name(tags, vpc["VpcId"]),
                resource_type="ec2:vpc",
                arn=f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc['VpcId']}",
                region=region, account_alias=account_alias, account_id=account_id,
                status=vpc["State"], tags=tags, raw=vpc,
            ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:vpc")


def collect_security_groups(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_security_groups")
        resources = []
        for page in paginator.paginate():
            for sg in page["SecurityGroups"]:
                tags = _tags(sg.get("Tags"))
                resources.append(AwsResource(
                    resource_id=sg["GroupId"],
                    name=_name(tags, sg["GroupName"]),
                    resource_type="ec2:security-group",
                    arn=f"arn:aws:ec2:{region}:{account_id}:security-group/{sg['GroupId']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags=tags, raw=sg,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:security-group")


def collect_subnets(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_subnets")
        resources = []
        for page in paginator.paginate():
            for subnet in page["Subnets"]:
                tags = _tags(subnet.get("Tags"))
                resources.append(AwsResource(
                    resource_id=subnet["SubnetId"], name=_name(tags, subnet["SubnetId"]),
                    resource_type="ec2:subnet",
                    arn=subnet.get("SubnetArn", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=subnet["State"], tags=tags, raw=subnet,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:subnet")


def collect_internet_gateways(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_internet_gateways")
        resources = []
        for page in paginator.paginate():
            for igw in page["InternetGateways"]:
                tags = _tags(igw.get("Tags"))
                state = "attached" if igw.get("Attachments") else "detached"
                resources.append(AwsResource(
                    resource_id=igw["InternetGatewayId"],
                    name=_name(tags, igw["InternetGatewayId"]),
                    resource_type="ec2:internet-gateway",
                    arn=f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw['InternetGatewayId']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=state, tags=tags, raw=igw,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:internet-gateway")


def collect_nat_gateways(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_nat_gateways")
        resources = []
        for page in paginator.paginate(Filter=[{"Name": "state", "Values": ["available"]}]):
            for ngw in page["NatGateways"]:
                tags = _tags(ngw.get("Tags"))
                resources.append(AwsResource(
                    resource_id=ngw["NatGatewayId"], name=_name(tags, ngw["NatGatewayId"]),
                    resource_type="ec2:nat-gateway",
                    arn=f"arn:aws:ec2:{region}:{account_id}:natgateway/{ngw['NatGatewayId']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=ngw["State"], tags=tags, raw=ngw,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:nat-gateway")


def collect_vpc_endpoints(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_vpc_endpoints")
        resources = []
        for page in paginator.paginate():
            for ep in page["VpcEndpoints"]:
                tags = _tags(ep.get("Tags"))
                resources.append(AwsResource(
                    resource_id=ep["VpcEndpointId"], name=_name(tags, ep["ServiceName"]),
                    resource_type="ec2:vpc-endpoint",
                    arn=f"arn:aws:ec2:{region}:{account_id}:vpc-endpoint/{ep['VpcEndpointId']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=ep["State"], tags=tags, raw=ep,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:vpc-endpoint")


def collect_transit_gateways(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("ec2", region_name=region)
        paginator = client.get_paginator("describe_transit_gateways")
        resources = []
        for page in paginator.paginate():
            for tgw in page["TransitGateways"]:
                tags = _tags(tgw.get("Tags"))
                resources.append(AwsResource(
                    resource_id=tgw["TransitGatewayId"], name=_name(tags, tgw["TransitGatewayId"]),
                    resource_type="ec2:transit-gateway",
                    arn=tgw.get("TransitGatewayArn", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=tgw["State"], tags=tags, raw=tgw,
                ))
        return resources
    return _safe(_collect, account_alias, region, "ec2:transit-gateway")


def collect_load_balancers_v2(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("elbv2", region_name=region)
        paginator = client.get_paginator("describe_load_balancers")
        resources = []
        for page in paginator.paginate():
            for lb in page["LoadBalancers"]:
                try:
                    tag_resp = client.describe_tags(ResourceArns=[lb["LoadBalancerArn"]])
                    tags = _tags(tag_resp["TagDescriptions"][0].get("Tags") if tag_resp["TagDescriptions"] else [])
                except ClientError:
                    tags = {}
                resources.append(AwsResource(
                    resource_id=lb["LoadBalancerName"], name=lb["LoadBalancerName"],
                    resource_type="elbv2:load-balancer",
                    arn=lb.get("LoadBalancerArn", ""),
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=lb["State"]["Code"], tags=tags, raw=lb,
                ))
        return resources
    return _safe(_collect, account_alias, region, "elbv2:load-balancer")


def collect_load_balancers_classic(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("elb", region_name=region)
        paginator = client.get_paginator("describe_load_balancers")
        resources = []
        for page in paginator.paginate():
            for lb in page["LoadBalancerDescriptions"]:
                resources.append(AwsResource(
                    resource_id=lb["LoadBalancerName"], name=lb["LoadBalancerName"],
                    resource_type="elb:load-balancer",
                    arn=f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb['LoadBalancerName']}",
                    region=region, account_alias=account_alias, account_id=account_id,
                    status="active", tags={}, raw=lb,
                ))
        return resources
    return _safe(_collect, account_alias, region, "elb:load-balancer")


def collect_acm_certificates(session: boto3.Session, account_alias: str, account_id: str, region: str) -> list[AwsResource]:
    def _collect():
        client = session.client("acm", region_name=region)
        paginator = client.get_paginator("list_certificates")
        resources = []
        for page in paginator.paginate():
            for cert in page["CertificateSummaryList"]:
                resources.append(AwsResource(
                    resource_id=cert["CertificateArn"].split("/")[-1],
                    name=cert.get("DomainName", cert["CertificateArn"].split("/")[-1]),
                    resource_type="acm:certificate",
                    arn=cert["CertificateArn"],
                    region=region, account_alias=account_alias, account_id=account_id,
                    status=cert.get("Status", "").lower(), tags={}, raw=cert,
                ))
        return resources
    return _safe(_collect, account_alias, region, "acm:certificate")


# ── main scan entry point ──────────────────────────────────────────────────

def get_enabled_regions(session: boto3.Session) -> list[str]:
    client = session.client("ec2", region_name="us-east-1")
    regions = client.describe_regions(
        Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}]
    )["Regions"]
    return [r["RegionName"] for r in regions]


def scan_account(session: boto3.Session, account_alias: str, account_id: str,
                 progress_callback=None) -> list[AwsResource]:
    regions = get_enabled_regions(session)
    all_resources: list[AwsResource] = []
    collected_globals: set[str] = set()

    def _progress(msg: str):
        if progress_callback:
            progress_callback(msg)

    # Global collectors — run once against us-east-1
    _progress(f"[{account_alias}] Collecting IAM...")
    all_resources.extend(collect_iam_users(session, account_alias, account_id))
    all_resources.extend(collect_iam_groups(session, account_alias, account_id))
    all_resources.extend(collect_iam_roles(session, account_alias, account_id))
    all_resources.extend(collect_iam_customer_policies(session, account_alias, account_id))
    collected_globals.update({"s3", "cloudfront", "route53"})

    _progress(f"[{account_alias}] Collecting global services (S3, CloudFront, Route53)...")
    all_resources.extend(collect_s3_buckets(session, account_alias, account_id))
    all_resources.extend(collect_cloudfront_distributions(session, account_alias, account_id))
    all_resources.extend(collect_route53_hosted_zones(session, account_alias, account_id))

    for region in regions:
        _progress(f"[{account_alias}/{region}] Scanning...")

        # Compute
        all_resources.extend(collect_ec2_instances(session, account_alias, account_id, region))
        all_resources.extend(collect_autoscaling_groups(session, account_alias, account_id, region))
        all_resources.extend(collect_lambda_functions(session, account_alias, account_id, region))
        all_resources.extend(collect_ecs_clusters(session, account_alias, account_id, region))
        all_resources.extend(collect_eks_clusters(session, account_alias, account_id, region))

        # Storage & DB
        all_resources.extend(collect_rds_instances(session, account_alias, account_id, region))
        all_resources.extend(collect_dynamodb_tables(session, account_alias, account_id, region))
        all_resources.extend(collect_elasticache_clusters(session, account_alias, account_id, region))
        all_resources.extend(collect_elasticache_replication_groups(session, account_alias, account_id, region))
        all_resources.extend(collect_redshift_clusters(session, account_alias, account_id, region))
        all_resources.extend(collect_opensearch_domains(session, account_alias, account_id, region))
        all_resources.extend(collect_kinesis_streams(session, account_alias, account_id, region))
        all_resources.extend(collect_ecr_repositories(session, account_alias, account_id, region))

        # Messaging
        all_resources.extend(collect_sqs_queues(session, account_alias, account_id, region))
        all_resources.extend(collect_sns_topics(session, account_alias, account_id, region))

        # Networking
        all_resources.extend(collect_vpcs(session, account_alias, account_id, region))
        all_resources.extend(collect_subnets(session, account_alias, account_id, region))
        all_resources.extend(collect_security_groups(session, account_alias, account_id, region))
        all_resources.extend(collect_internet_gateways(session, account_alias, account_id, region))
        all_resources.extend(collect_nat_gateways(session, account_alias, account_id, region))
        all_resources.extend(collect_vpc_endpoints(session, account_alias, account_id, region))
        all_resources.extend(collect_transit_gateways(session, account_alias, account_id, region))
        all_resources.extend(collect_load_balancers_v2(session, account_alias, account_id, region))
        all_resources.extend(collect_load_balancers_classic(session, account_alias, account_id, region))

        # API & Security
        all_resources.extend(collect_apigateway_rest_apis(session, account_alias, account_id, region))
        all_resources.extend(collect_apigatewayv2_http_apis(session, account_alias, account_id, region))
        all_resources.extend(collect_acm_certificates(session, account_alias, account_id, region))
        all_resources.extend(collect_secretsmanager_secrets(session, account_alias, account_id, region))

    return all_resources
