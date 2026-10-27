"""Curated learning-resource catalogue (official docs and reputable free material).

Links point to well-known official documentation and free learning platforms. Users can
edit or replace them. This is guidance, not an endorsement or a guarantee.
"""
from __future__ import annotations

RESOURCE_CATALOG: dict[str, list[dict]] = {
    "python": [
        {"title": "The Python Tutorial (official)", "url": "https://docs.python.org/3/tutorial/", "kind": "docs", "provider": "Python Software Foundation", "is_free": True},
        {"title": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com/", "kind": "book", "provider": "Al Sweigart", "is_free": True},
    ],
    "javascript": [
        {"title": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "kind": "docs", "provider": "MDN", "is_free": True},
    ],
    "typescript": [
        {"title": "TypeScript Handbook (official)", "url": "https://www.typescriptlang.org/docs/handbook/intro.html", "kind": "docs", "provider": "Microsoft", "is_free": True},
    ],
    "react": [
        {"title": "React Learn (official)", "url": "https://react.dev/learn", "kind": "docs", "provider": "Meta", "is_free": True},
    ],
    "node.js": [
        {"title": "Node.js Learn", "url": "https://nodejs.org/en/learn", "kind": "docs", "provider": "OpenJS", "is_free": True},
    ],
    "fastapi": [
        {"title": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com/tutorial/", "kind": "docs", "provider": "Sebastián Ramírez", "is_free": True},
    ],
    "django": [
        {"title": "Django Tutorial (official)", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "kind": "docs", "provider": "Django Software Foundation", "is_free": True},
    ],
    "sql": [
        {"title": "SQLBolt — interactive SQL", "url": "https://sqlbolt.com/", "kind": "tutorial", "provider": "SQLBolt", "is_free": True},
        {"title": "PostgreSQL Tutorial (official)", "url": "https://www.postgresql.org/docs/current/tutorial.html", "kind": "docs", "provider": "PostgreSQL", "is_free": True},
    ],
    "postgresql": [
        {"title": "PostgreSQL Tutorial (official)", "url": "https://www.postgresql.org/docs/current/tutorial.html", "kind": "docs", "provider": "PostgreSQL", "is_free": True},
    ],
    "docker": [
        {"title": "Docker Get Started", "url": "https://docs.docker.com/get-started/", "kind": "docs", "provider": "Docker", "is_free": True},
    ],
    "kubernetes": [
        {"title": "Kubernetes Basics (official)", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "kind": "docs", "provider": "CNCF", "is_free": True},
    ],
    "terraform": [
        {"title": "Terraform Tutorials", "url": "https://developer.hashicorp.com/terraform/tutorials", "kind": "docs", "provider": "HashiCorp", "is_free": True},
    ],
    "aws": [
        {"title": "AWS Skill Builder", "url": "https://skillbuilder.aws/", "kind": "course", "provider": "AWS", "is_free": True},
        {"title": "AWS Cloud Practitioner Essentials", "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/", "kind": "course", "provider": "AWS", "is_free": True},
    ],
    "machine learning": [
        {"title": "Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course", "kind": "course", "provider": "Google", "is_free": True},
        {"title": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html", "kind": "docs", "provider": "scikit-learn", "is_free": True},
    ],
    "pytorch": [
        {"title": "PyTorch Tutorials (official)", "url": "https://pytorch.org/tutorials/", "kind": "docs", "provider": "PyTorch", "is_free": True},
    ],
    "tensorflow": [
        {"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials", "kind": "docs", "provider": "Google", "is_free": True},
    ],
    "git": [
        {"title": "Pro Git (free book)", "url": "https://git-scm.com/book/en/v2", "kind": "book", "provider": "git-scm.com", "is_free": True},
    ],
    "linux": [
        {"title": "The Linux Command Line (free book)", "url": "https://linuxcommand.org/tlcl.php", "kind": "book", "provider": "William Shotts", "is_free": True},
    ],
    "data structures": [
        {"title": "MIT 6.006 Introduction to Algorithms", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "kind": "course", "provider": "MIT OpenCourseWare", "is_free": True},
    ],
    "algorithms": [
        {"title": "MIT 6.006 Introduction to Algorithms", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "kind": "course", "provider": "MIT OpenCourseWare", "is_free": True},
    ],
    "system design": [
        {"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "kind": "tutorial", "provider": "GitHub", "is_free": True},
    ],
}

DEFAULT_RESOURCES = [
    {"title": "MDN Web Docs", "url": "https://developer.mozilla.org/", "kind": "docs", "provider": "MDN", "is_free": True},
    {"title": "freeCodeCamp Curriculum", "url": "https://www.freecodecamp.org/learn/", "kind": "course", "provider": "freeCodeCamp", "is_free": True},
]


def resources_for(skill: str) -> list[dict]:
    key = skill.strip().lower()
    if key in RESOURCE_CATALOG:
        return RESOURCE_CATALOG[key]
    for known, resources in RESOURCE_CATALOG.items():
        if known in key or key in known:
            return resources
    return DEFAULT_RESOURCES[:1]
