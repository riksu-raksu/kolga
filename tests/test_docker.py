import tempfile
from pathlib import Path
from typing import List

import docker.errors
import pytest

from scripts.libs.docker import Docker
from scripts.settings import settings


def test_incorrect_dockerfile_path() -> None:
    dockerfile_path = "/i_do_not_exist/Dockerfile"
    with pytest.raises(FileNotFoundError):
        Docker(dockerfile_path)


@pytest.mark.parametrize(  # type: ignore
    "value, expected",
    [
        ("FROM python,3.6-slim AS base\n" "FROM base as testing", 2),
        ("FROM python,3.6-slim AS base", 1),
        ("FROM python,3.6-slim", 1),
        ("FROM python", 1),
        ("FROM", 0),
        ("AS base", 0),
        ("python,3.6-slim AS base", 0),
    ],
)
def test_get_stages_from_line(value: str, expected: int) -> None:
    d = Docker()

    test_strings = {value: expected, value.lower(): expected, value.upper(): expected}

    for string, result in test_strings.items():
        with tempfile.NamedTemporaryFile() as f:
            encoded_string = str.encode(string, encoding="UTF-8")
            f.write(encoded_string)
            f.seek(0)
            f.seek(0)
            d.dockerfile = Path(f.name)
            assert len(d.get_stages()) == result


@pytest.mark.parametrize(  # type: ignore
    "value, expected",
    [
        ("FROM python:3.6-slim AS APPBASE", ["APPBASE"]),
        ("FROM python:3.6-slim AS _23baseFs", ["_23baseFs"]),
        ("FROM python,3.6-slim AS base", ["base"]),
        ("FROM python,3.6-slim", [""]),
        ("FROM python", [""]),
        ("FROM", []),
        ("lizard", []),
    ],
)
def test_get_stages_names(value: str, expected: List[str]) -> None:
    d = Docker()

    with tempfile.NamedTemporaryFile() as f:
        encoded_string = str.encode(value, encoding="UTF-8")
        f.write(encoded_string)
        f.seek(0)
        d.dockerfile = Path(f.name)
        assert d.get_stages() == expected


@pytest.mark.parametrize(  # type: ignore
    "value, expected",
    [
        ("dash-test", "dash-test"),
        ("underscore_test", "underscore-test"),
        ("slash/test", "slash-test"),
    ],
)
def test_get_docker_git_ref_tag_values(value: str, expected: str) -> None:
    assert Docker.get_docker_git_ref_tag(value) == expected


@pytest.mark.parametrize(  # type: ignore
    "stage, final_image, expected_amount",
    [("", False, 2), ("", True, 2), ("nonfinal", False, 2), ("final", True, 4)],
)
def test_get_image_tags_amount(
    stage: str, final_image: bool, expected_amount: int
) -> None:
    d = Docker()
    images_tags = d.get_image_tags(stage=stage, final_image=final_image)
    assert len(images_tags) == expected_amount


@pytest.mark.parametrize(  # type: ignore
    "stage, final_image, expected_tags",
    [
        (
            "",
            False,
            [
                settings.GIT_COMMIT_SHA,
                Docker.get_docker_git_ref_tag(settings.GIT_COMMIT_REF_NAME),
            ],
        ),
        (
            "",
            True,
            [
                settings.GIT_COMMIT_SHA,
                Docker.get_docker_git_ref_tag(settings.GIT_COMMIT_REF_NAME),
            ],
        ),
        (
            "nonfinal",
            False,
            [
                f"{settings.GIT_COMMIT_SHA}-nonfinal",
                f"{Docker.get_docker_git_ref_tag(settings.GIT_COMMIT_REF_NAME)}-nonfinal",
            ],
        ),
        (
            "final",
            True,
            [
                f"{settings.GIT_COMMIT_SHA}-final",
                f"{Docker.get_docker_git_ref_tag(settings.GIT_COMMIT_REF_NAME)}-final",
                f"{settings.GIT_COMMIT_SHA}",
                f"{Docker.get_docker_git_ref_tag(settings.GIT_COMMIT_REF_NAME)}",
            ],
        ),
    ],
)
def test_get_image_tags_name(
    stage: str, final_image: bool, expected_tags: List[str]
) -> None:
    d = Docker()
    images_tags = d.get_image_tags(stage=stage, final_image=final_image)
    assert images_tags == sorted(expected_tags)


# =====================================================
# DOCKER REGISTRY REQUIRED FROM THIS POINT FORWARD
# =====================================================


def test_login() -> None:
    d = Docker()
    d.login()


def test_incorrect_login() -> None:
    d = Docker()
    with pytest.raises(docker.errors.APIError):
        d.login(password="bad_login")


def test_build_push_delete_pull_images() -> None:
    d = Docker()
    d.login()

    images = d.build_stages()
    d.push_images(images)

    # Remove any local cache
    for image in images:
        d.delete_image(image)

    for image in images:
        for tag in image.remote_tags:
            d.pull_image(f"{image.repository}:{tag}", error_on_not_found=True)
