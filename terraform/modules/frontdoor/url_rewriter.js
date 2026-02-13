function handler(event) {
    const exceptions = ["signout","confirm-sign-out", "error", "assets", "id-verification", "logout", "oauth2", "healthcheck", "cookies", "maintenance", ".well-known"];
    const request = event.request;
    const hostName = request.headers.host.value;
    let pathSegments = request.uri.split('/');

    if (!url_should_be_rewritten(pathSegments, hostName, exceptions)) {
        return request;
    }

    pathSegments = insert_service_segment_for_domain(pathSegments, hostName);

    request.uri = pathSegments.join('/');
    return request
}

function insert_service_segment_for_domain(pathSegments, hostName) {
    if (hostName.includes("register-home-to-rent")) {
        pathSegments.splice(1,0,"landlord");
    }

    if (hostName.includes("search-landlord-home-information")) {
        pathSegments.splice(1,0,"local-council");
    }
    return pathSegments;
}

function url_should_be_rewritten(pathSegments, hostName, exceptions) {
    return !(exceptions.includes(pathSegments[1]) ||
        (hostName.includes("register-home-to-rent") && pathSegments[1] === "landlord") ||
        (hostName.includes("search-landlord-home-information") && pathSegments[1] === "local-council"));
}