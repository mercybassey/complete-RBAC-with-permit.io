## Introduction

This repository is a Flask application that was used to demonstrate how to enforce Role-based access control with Permit.io in an article titled "[How to Build an RBAC Permissioned Admin Dashboard with Permit.io and Flask](https://medium.com/javascript-in-plain-english/how-to-build-an-rbac-permissioned-admin-dashboard-with-permit-io-and-flask-a5503a907dad)".

## Prerequisites
- A [permit.io](http://permit.io) account with a project already created. 
- An [Auth0 account](https://auth0.com/signup?place=header&type=button&text=sign%20up) with an [application](https://auth0.com/docs/get-started/auth0-overview/create-applications) already set up. 
- [Docker](https://www.docker.com/) installed on your machine, to deploy Permits’ [policy decision point.](https://docs.permit.io/concepts/pdp/overview/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Poetry](https://python-poetry.org/docs/#installing-with-pipx) installed on your machine.

## Setup

1. Clone the repository.

```bash
    $ git clone git@github.com:mercybassey/complete-RBAC-with-permit.io.git
    $ cd complete-RBAC-with-permit.io
```

2. Create and activate a Poetry shell:

```bash
    $ poetry shell
```
3. Install all dependencies:

```bash
    $ poetry install
```

4. Create a `.env` file and Set up environment variables:

```bash
    SECRET_KEY="<randomly generated key>"
    PDP_API_KEY="<permit-project-environment-api-key"
    AUTH0_DOMAIN="<Auth0-application-domain>"
    AUTH0_CLIENT_ID="<client-id-for-your-auth0-application>"
    AUTH0_CLIENT_SECRET="<clent-secret-associated-with-your-auth0-client-id>"
    AUTH0_CALLBACK_URL="http://localhost:5000/login/callback"
```

## Usage

- Open the application in your browser at http://127.0.0.1:5000/.
- Log in as an `admininstrator`.
- Test different role-based scenarios by creating users with specific roles.
