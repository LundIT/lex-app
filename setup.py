from setuptools import setup, find_packages

setup(
    name="dpag",
    version="1.0.0",
    author="Melih Sünbül",
    author_email="m.sunbul@lund-it.com",
    description="A Python / Django library to create business applications easily with complex logic",
    long_description_content_type="text/markdown",
    url="https://github.com/LundIT/dpag-pip",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'dpag = dpag.__main__:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "wheel",
        "django~=4.1.10",
        "django-rest-framework",
        "django-cors-headers",
        "djangorestframework-simplejwt",
        "djangorestframework-api-key @ git+https://github.com/LundIT/djangorestframework-api-key",
        "django-filter",
        "django-extensions",
        "drf-oidc-auth @ git+https://github.com/LundIT/drf-oidc-auth",
        "mozilla-django-oidc",
        "XlsxWriter==1.3.9",
        "scipy",
        "numpy",
        "pandas==1.4.3",
        "openpyxl",
        "psycopg2-binary",
        "pdfkit~=0.6.1",
        "django-allow-cidr",
        "django-cprofile-middleware",
        "pretty_html_table",
        "djangorestframework~=3.13.1",
        "setuptools~=65.5.1",
        "requests~=2.31.0",
        "django-sendgrid-v5",
        "redis",
        "celery",
        "webdriver-manager==3.8.6",
        "sentry_sdk",
        "channels",
        "asyncio",
        "channels-redis",
        "uvicorn[standard]",
        "nest_asyncio",
        "Office365-REST-Python-Client",
        "streamlit",
        "streamlit-keycloak",
        "amqp",
        "sqlalchemy",
        "django_redis",
        "django-storages[google]",
        "DjangoSharepointStorage"
    ],
    scripts=['bin/dpag'],
    python_requires='>=3.6',
)
