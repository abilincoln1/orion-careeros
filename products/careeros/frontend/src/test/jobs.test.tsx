import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { JobsPage } from "../pages/JobsPage";
import * as api from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof api>("../api/client");
  return { ...actual, getJobListings: vi.fn(), discoverJobs: vi.fn() };
});

const DISCLOSED_LISTING: api.JobListingRead = {
  id: "1", title: "Systems Engineer", company_name_raw: "Acme Corp", location_raw: "Birmingham",
  is_remote: false, salary_min: 45000, salary_max: 60000, salary_currency: "GBP", salary_disclosed: true,
  description_raw: null, source_url: "https://example.com/job-1", posted_at: "2026-08-15T11:09:42+00:00",
  discovered_at: "2026-08-15T12:00:00+00:00",
};

const UNDISCLOSED_LISTING: api.JobListingRead = {
  ...DISCLOSED_LISTING, id: "2", title: "Cloud Engineer", salary_min: null, salary_max: null,
  salary_currency: null, salary_disclosed: false,
};

beforeEach(() => vi.clearAllMocks());

describe("JobsPage", () => {
  it("shows loading state, then empty state when no listings exist", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    render(<JobsPage />);
    expect(screen.getByText(/loading job listings/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/no job listings yet/i)).toBeInTheDocument());
  });

  it("renders real listing data returned by the API", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [DISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByText("Systems Engineer")).toBeInTheDocument());
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Birmingham")).toBeInTheDocument();
  });

  it("shows an API error state on failure, not a blank page", async () => {
    vi.mocked(api.getJobListings).mockRejectedValue(new api.ApiError(500, { error: { message: "Internal error" } }));
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  it("displays disclosed salary with real min/max/currency", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [DISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByText(/GBP 45,000/)).toBeInTheDocument());
  });

  it("SALARY HONESTY: shows 'not disclosed', never fabricates a value or implies a match", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [UNDISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() => expect(screen.getAllByText(/salary not disclosed/i).length).toBeGreaterThan(0));
    // Must never render any "matched"/"meets requirement" style claim.
    expect(screen.queryByText(/matched/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/meets.*requirement/i)).not.toBeInTheDocument();
  });

  it("SALARY HONESTY: the configured preference is shown as a preference, not active filtering", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() =>
      expect(screen.getByText(/cannot currently be used to filter results/i)).toBeInTheDocument()
    );
  });

  it("posted_at is displayed when supplied by the API", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [DISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() => expect(screen.getByText(/posted:/i)).toBeInTheDocument());
  });

  it("external job link opens the real source_url safely (noopener/noreferrer)", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [DISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    render(<JobsPage />);
    await waitFor(() => screen.getByText(/view original listing/i));
    const link = screen.getByText(/view original listing/i).closest("a")!;
    expect(link).toHaveAttribute("href", "https://example.com/job-1");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("Discover Jobs button triggers a real discovery request and refreshes listings", async () => {
    vi.mocked(api.getJobListings)
      .mockResolvedValueOnce({ items: [], total: 0, limit: 50, offset: 0 })
      .mockResolvedValueOnce({ items: [DISCLOSED_LISTING], total: 1, limit: 50, offset: 0 });
    vi.mocked(api.discoverJobs).mockResolvedValue({
      provider_name: "arbeitnow", query_used: "Systems Engineer", listings_found: 1, listings_new: 1, listings_duplicate: 0,
    });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText(/no job listings yet/i));
    await user.click(screen.getByText("Discover Jobs"));
    await waitFor(() => expect(screen.getByText(/found 1 listing/i)).toBeInTheDocument());
    expect(api.discoverJobs).toHaveBeenCalledOnce();
    // The actual search term must be visible -- previously captured
    // but never shown, making it impossible to diagnose whether
    // results came from a real, CV-derived query.
    expect(screen.getByText(/"Systems Engineer"/)).toBeInTheDocument();
  });

  it("shows an honest message when no search term was derived at all", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    vi.mocked(api.discoverJobs).mockResolvedValue({
      provider_name: "arbeitnow", query_used: "", listings_found: 175, listings_new: 0, listings_duplicate: 175,
    });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText(/no job listings yet/i));
    await user.click(screen.getByText("Discover Jobs"));
    await waitFor(() => expect(screen.getByText(/none -- returned the provider's unfiltered results/i)).toBeInTheDocument());
  });

  it("shows a clear error if the discovery request (provider) fails", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    vi.mocked(api.discoverJobs).mockRejectedValue(new api.ApiError(502, { error: { message: "Job provider request failed" } }));
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText(/no job listings yet/i));
    await user.click(screen.getByText("Discover Jobs"));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  // Location/remote filtering -- added after the initial UI MVP
  // walkthrough surfaced that the location field, while supported by
  // the backend, was never exposed in the UI at all.
  const UK_LISTING: api.JobListingRead = {
    ...DISCLOSED_LISTING, id: "3", title: "UK Systems Engineer", location_raw: "Birmingham, UK", is_remote: false,
  };
  const GERMAN_LISTING: api.JobListingRead = {
    ...DISCLOSED_LISTING, id: "4", title: "German Role", location_raw: "Berlin, Germany", is_remote: false,
  };
  const REMOTE_LISTING: api.JobListingRead = {
    ...DISCLOSED_LISTING, id: "5", title: "Remote Role", location_raw: null, is_remote: true,
  };

  it("filters listings by a real, case-insensitive location substring match", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [UK_LISTING, GERMAN_LISTING], total: 2, limit: 500, offset: 0 });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText("UK Systems Engineer"));
    expect(screen.getByText("German Role")).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/birmingham/i);
    await user.type(input, "birmingham");

    await waitFor(() => expect(screen.queryByText("German Role")).not.toBeInTheDocument());
    expect(screen.getByText("UK Systems Engineer")).toBeInTheDocument();
  });

  it("CORRECTED: a remote listing with no location connection to the search term is excluded, not shown regardless", async () => {
    // REMOTE_LISTING has location_raw: null -- no genuine connection
    // to "birmingham" exists, so it must not appear. This reverses
    // the earlier, real-world-tested-and-found-wrong assumption that
    // any remote listing should bypass a location filter.
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [GERMAN_LISTING, REMOTE_LISTING], total: 2, limit: 500, offset: 0 });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText("German Role"));

    const input = screen.getByPlaceholderText(/birmingham/i);
    await user.type(input, "birmingham");

    await waitFor(() => expect(screen.queryByText("German Role")).not.toBeInTheDocument());
    expect(screen.queryByText("Remote Role")).not.toBeInTheDocument();
  });

  it("a remote listing WITH real matching location text is still correctly included", async () => {
    const UK_REMOTE_LISTING: api.JobListingRead = {
      ...DISCLOSED_LISTING, id: "6", title: "UK Remote Role", location_raw: "United Kingdom - Remote", is_remote: true,
    };
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [GERMAN_LISTING, UK_REMOTE_LISTING], total: 2, limit: 500, offset: 0 });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText("German Role"));

    const input = screen.getByPlaceholderText(/birmingham/i);
    await user.type(input, "united kingdom");

    await waitFor(() => expect(screen.queryByText("German Role")).not.toBeInTheDocument());
    expect(screen.getByText("UK Remote Role")).toBeInTheDocument();
  });

  it("Remote only checkbox excludes non-remote listings", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [UK_LISTING, REMOTE_LISTING], total: 2, limit: 500, offset: 0 });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText("UK Systems Engineer"));

    await user.click(screen.getByLabelText(/remote only/i));

    await waitFor(() => expect(screen.queryByText("UK Systems Engineer")).not.toBeInTheDocument());
    expect(screen.getByText("Remote Role")).toBeInTheDocument();
  });

  it("HONESTY: states plainly that this is text matching, not a real distance/postcode search", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 500, offset: 0 });
    render(<JobsPage />);
    await waitFor(() =>
      expect(screen.getByText(/not a real distance\/postcode radius search/i)).toBeInTheDocument()
    );
  });

  it("Discover Jobs passes the current location/remote filter values to the real API call", async () => {
    vi.mocked(api.getJobListings).mockResolvedValue({ items: [], total: 0, limit: 500, offset: 0 });
    vi.mocked(api.discoverJobs).mockResolvedValue({
      provider_name: "arbeitnow", query_used: "", listings_found: 0, listings_new: 0, listings_duplicate: 0,
    });
    const user = userEvent.setup();
    render(<JobsPage />);
    await waitFor(() => screen.getByText(/no job listings yet/i));

    await user.type(screen.getByPlaceholderText(/birmingham/i), "Birmingham");
    await user.click(screen.getByLabelText(/remote only/i));
    await user.click(screen.getByText("Discover Jobs"));

    await waitFor(() =>
      expect(api.discoverJobs).toHaveBeenCalledWith({ location: "Birmingham", remote_only: true })
    );
  });
});
