# URL Rewriter

url_writer is a cloudfront function that inserts a service path segment (i.e. `/landlord` or `/local-council`) into the request URL.

## Excluded endpoints
Endpoints which are common between services such as `/error` and `/signout` are excluded from the rewriting, so do not include the service name.
Endpoints that Spring generates for us (e.g. those use for authentication) are also excluded.

## Unit tests
We now have unit tests for this function.

Cloudfront functions cannot be exported as a module, so unit tests have been written using the 'require' syntax.
The 'rewire' package is used to access the handler function in the url_rewriter.js file.

## AWS console tests

The function can also be manually tested on AWS Console (see [documentation here](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/test-function.html)). This gives an indication of whether the function is fast enough (the "compute utilisation" output should be below 50 to be safe)

To test the function
- Go to AWS Console and go to the Cloudfront service.
- From the menu on the left, select "Functions" and then select the `url_rewriter` function.
- Select the "Test" tab.
- Create a new test event (or use an existing one) with:
  - Event type: Viewer request
  - Stage: Live to test the deployed version
  - Request
    - HTTP method: GET
    - URL path: endpoint, not including the domain, e.g. `/dashboard`
    - Add the domain by adding a request header with the name `Host` and value of the domain name, e.g. `https://integration.register-home-to-rent.test.communities.gov.uk``

You can either save this function to use it again later, or just run it but clicking the "Test function" button.
- Check that the output is as expected in the "Execution result" section.
- Check that "Compute utilisation" is below 50.

You can look in url_rewriter.test.js for examples of urls to test.