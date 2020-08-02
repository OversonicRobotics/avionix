import os
from pathlib import Path
import re
import shutil

from avionix import ChartBuilder, ChartDependency, ChartInfo
from avionix.chart.chart_builder import get_helm_installations
from avionix.kubernetes_objects.apps import Deployment
from avionix.testing import kubectl_get
from avionix.testing.installation_context import ChartInstallationContext


def test_chart_folder_building(test_deployment1: Deployment):
    test_folder = Path("tmp")
    os.makedirs(test_folder, exist_ok=True)
    builder = ChartBuilder(
        ChartInfo(api_version="3.2.4", name="test", version="0.1.0"),
        [test_deployment1, test_deployment1],
        test_folder,
    )
    builder.generate_chart()
    templates_folder = test_folder / builder.chart_info.name / "templates"

    for file in os.listdir(templates_folder):
        with open(templates_folder / Path(file)) as kube_file:
            assert kube_file.read() == str(test_deployment1)

        assert re.match(rf"{test_deployment1.kind}-[0-9]+\.yaml", file)
    shutil.rmtree(test_folder)


def test_chart_installation(config_map):
    builder = ChartBuilder(
        ChartInfo(api_version="3.2.4", name="test", version="0.1.0", app_version="v1"),
        [config_map],
    )
    with ChartInstallationContext(builder):
        # Check helm release
        helm_installation = get_helm_installations()
        assert helm_installation["NAME"][0] == "test"
        assert helm_installation["REVISION"][0] == "1"
        assert helm_installation["STATUS"][0] == "deployed"

        assert builder.is_installed

        config_maps = kubectl_get("configmaps")
        assert config_maps["NAME"][0] == "test-config-map"
        assert config_maps["DATA"][0] == "1"


def test_chart_w_dependencies():
    builder = ChartBuilder(
        ChartInfo(
            api_version="3.2.4",
            name="test",
            version="0.1.0",
            app_version="v1",
            dependencies=[
                ChartDependency(
                    name="kubernetes-dashboard",
                    version="2.3.0",
                    repository="https://kubernetes.github.io/dashboard",
                    local_repo_name="k8s-dashboard",
                    values={"rbac": {"clusterReadOnlyRole": True}},
                )
            ],
        ),
        [],
        keep_chart=True,
    )
    with ChartInstallationContext(builder):
        # Check helm release
        helm_installation = get_helm_installations()
        assert helm_installation["NAME"][0] == "test"
        assert helm_installation["REVISION"][0] == "1"
        assert helm_installation["STATUS"][0] == "deployed"

        assert builder.is_installed


def test_installation_with_namespace(chart_info):
    builder = ChartBuilder(chart_info, [], namespace="test", create_namespace=True)
    with ChartInstallationContext(builder):
        # Check helm release
        helm_installation = get_helm_installations("test")
        assert helm_installation["NAME"][0] == "test"
        assert helm_installation["REVISION"][0] == "1"
        assert helm_installation["STATUS"][0] == "deployed"
        assert helm_installation["NAMESPACE"][0] == "test"


def test_installing_two_components(
    config_map, config_map2, chart_info: ChartInfo,
):
    config_map.metadata.name = "test-config-map-1"
    builder = ChartBuilder(chart_info, [config_map, config_map2],)
    with ChartInstallationContext(builder):
        # Check helm release
        helm_installation = get_helm_installations()
        assert helm_installation["NAME"][0] == "test"
        assert helm_installation["REVISION"][0] == "1"
        assert helm_installation["STATUS"][0] == "deployed"

        # Check kubernetes components
        config_maps = kubectl_get("configmaps")
        for i in range(2):
            assert config_maps["NAME"][i] == f"test-config-map-{i + 1}"
            assert config_maps["DATA"][i] == "1"
