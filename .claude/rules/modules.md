---
paths:
  - "plugins/**"
  - "tests/**"
---

# Module and Test Implementation Rules

## 1. General principles

- Follow the project's `CLAUDE.md` and all applicable rules.
- Write all source code, module documentation, test descriptions, and comments in English.
- Follow established Ansible module conventions and the repository's existing structure.
- Keep modules focused on a single resource or operation.
- Prefer simple, explicit implementations over unnecessary abstractions.
- Do not introduce runtime dependencies without documenting the need and obtaining approval.
- Do not modify unrelated files or existing behavior without justification.

## 2. API contract and sources

- Use official Magalu Cloud API documentation as the source of truth for API behavior.
- Use `amazon.aws` and `google.cloud` only as references for Ansible interface conventions, not as evidence of Magalu Cloud capabilities.
- Before implementing an operation, identify its documented endpoint, HTTP method, authentication requirements, parameters, response structure, and error behavior.
- Do not invent endpoints, parameters, defaults, lifecycle states, response fields, or resource capabilities.
- If required information is missing or contradictory, stop the affected implementation and report the unresolved question.
- Use `# TODO(source): <missing information>` for specific API-contract gaps in working code, when appropriate. Do not use TODOs to justify shipping a nonfunctional implementation.
- Keep official source URLs in relevant development notes or other appropriate documentation.

## 3. Module responsibilities and structure

- Place Ansible modules in `plugins/modules/`.
- Place genuinely reusable module utilities in `plugins/module_utils/`.
- Keep API communication, authentication, and shared error handling consistent across modules where practical.
- Do not introduce shared abstractions before there is a concrete need.
- Separate read-only information modules from resource lifecycle modules.
- Use the `_info` suffix for read-only information modules, following established Ansible conventions.
- Do not make read-only modules mutate resources.
- Follow the repository's existing naming conventions and collection layout.

## 4. Module interface and documentation

- Define module arguments using Ansible's supported module argument specification.
- Explicitly document required arguments, types, defaults, choices, and secret fields.
- Do not define a default unless it is supported by the API contract or is an intentional, documented module-level behavior.
- Document return values, including their types and meanings.
- Include realistic YAML examples and examples of returned data.
- Document important failure cases and state semantics.
- Use `AnsibleModule` and standard Ansible module conventions rather than implementing a custom module execution framework.
- Ensure successful execution returns structured data and an accurate `changed` value.
- Do not expose credentials, authorization headers, or other secrets in output or error messages.

## 5. Resource lifecycle and idempotency

- Implement only lifecycle operations supported by the documented Magalu Cloud API.
- Use `state: present` and `state: absent` only when their semantics can be implemented correctly for the resource.
- Do not add `started`, `stopped`, `restarted`, or other states without a documented API capability and a clear module contract.
- Determine whether the desired state already exists before reporting a change, when the API provides sufficient information.
- Repeated execution with the same desired state should not report a change when no change is needed.
- Do not report a successful state transition until the API response or a documented follow-up check supports it.
- Respect immutable fields and asynchronous operations according to the official API contract.
- Never interpret authentication, permission, timeout, or server errors as proof that a resource does not exist.
- Do not retry non-idempotent operations unless their retry safety is established.

## 6. Check mode and execution behavior

- Declare and implement check-mode support only when the module can safely predict changes without performing mutations.
- In check mode, do not execute API operations that create, modify, delete, start, stop, or otherwise mutate resources.
- Read-only requests may be used in check mode when needed to determine the current state.
- When the desired change cannot be determined safely, explain the limitation instead of claiming an accurate prediction.
- Validate inputs before making unnecessary API requests.
- Avoid unnecessary API calls and do not silently ignore failed operations.

## 7. Authentication, HTTP, and error handling

- Follow the documented Magalu Cloud authentication mechanism and endpoint for each product.
- Never hardcode credentials or send them to untrusted endpoints.
- Use the repository's approved shared HTTP utilities when available; do not duplicate authentication and transport logic unnecessarily.
- Use Ansible-supported HTTP and URL handling facilities where appropriate.
- Handle HTTP errors, connection failures, timeouts, and malformed responses explicitly.
- Preserve useful diagnostic information without leaking secrets.
- Use `no_log` for tasks or module argument specifications involving sensitive values where appropriate.
- Do not follow redirects that could disclose credentials to an untrusted destination.
- Do not invent retry policies, timeouts, TLS behavior, or environment-variable conventions without an established project contract.

## 8. Testing requirements

- Add unit tests for every new module and meaningful shared utility.
- Mock HTTP interactions in unit tests; unit tests must not require live cloud resources or real credentials.
- Cover successful responses, invalid inputs, authentication and permission failures, connection errors, server errors, and malformed responses where applicable.
- For lifecycle modules, test resource creation, existing desired state, necessary changes, deletion, and repeated execution as applicable to the documented API.
- Test check-mode behavior for modules that support it, ensuring no mutations occur.
- Test that secrets are not exposed in module output or error messages.
- Keep tests deterministic and independent of execution order.
- Do not add integration tests that create, modify, or delete real cloud resources without explicit authorization.

## 9. Validation and completion

- Run the relevant unit tests and Ansible validation tools available in the development environment.
- Use `ansible-test sanity` and `ansible-lint` where applicable.
- Do not claim that a test or validation passed unless it was actually executed successfully.
- Report commands executed, results, known limitations, and unresolved API-contract questions.
- Do not suppress failures or weaken tests merely to obtain a passing result.