import { useEffect, useMemo, useState } from "react";
import * as api from "../api/client";
import { ErrorState, LoadingState, EmptyState } from "../components/StateViews";

function SalaryDisplay({ listing }: { listing: api.JobListingRead }) {
  // Per directive Section 8: never imply Arbeitnow is filtering by
  // salary, never fabricate a value, never show a false "salary
  // matched" status. If undisclosed, say so plainly.
  if (!listing.salary_disclosed) {
    return <span style={{ color: "#777" }}>Salary not disclosed</span>;
  }
  const min = listing.salary_min;
  const max = listing.salary_max;
  const currency = listing.salary_currency ?? "";
  if (min !== null && max !== null) {
    return <span>{currency} {min.toLocaleString()} &ndash; {max.toLocaleString()}</span>;
  }
  if (min !== null) return <span>{currency} {min.toLocaleString()}+</span>;
  return <span style={{ color: "#777" }}>Salary not disclosed</span>;
}

export function JobsPage() {
  const [listings, setListings] = useState<api.JobListingRead[] | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discoveryResult, setDiscoveryResult] = useState<api.DiscoveryResponse | null>(null);
  const [discoveryError, setDiscoveryError] = useState<unknown>(null);

  // Real filter state. This is a plain, case-insensitive substring
  // match against each listing's real location_raw text -- there is
  // no postcode/coordinate geocoding or actual distance calculation
  // anywhere in this system. Stated in the UI itself, not just here,
  // so this is never oversold as a true "25 mile radius" search.
  const [locationFilter, setLocationFilter] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);

  async function loadListings() {
    try {
      // Fetch the full set (limit high enough to cover the real
      // current total, capped at the backend's own le=200 constraint
      // on this endpoint -- confirmed against the actual API code,
      // not guessed) so client-side filtering works against
      // everything you actually have, not just the first page.
      const page = await api.getJobListings(200, 0);
      setListings(page.items);
      setTotal(page.total);
    } catch (err) {
      setError(err);
    }
  }

  useEffect(() => {
    loadListings();
  }, []);

  const filteredListings = useMemo(() => {
    if (listings === null) return null;
    return listings.filter((listing) => {
      if (remoteOnly && !listing.is_remote) return false;
      if (locationFilter.trim()) {
        const needle = locationFilter.trim().toLowerCase();
        const haystack = (listing.location_raw ?? "").toLowerCase();
        // Corrected after real-world testing: a remote listing does
        // NOT automatically pass a location filter. "Remote" does not
        // mean "based in the UK" -- a German company's remote role
        // has no real connection to a Birmingham search, and letting
        // it through cluttered results with irrelevant listings. The
        // location filter now applies uniformly to location_raw text
        // for every listing; a remote UK role (e.g. "United Kingdom -
        // Remote", seen in real Arbeitnow data) correctly still
        // matches "UK" because that text is genuinely present.
        if (!haystack.includes(needle)) return false;
      }
      return true;
    });
  }, [listings, locationFilter, remoteOnly]);

  async function handleDiscover() {
    setDiscovering(true);
    setDiscoveryError(null);
    setDiscoveryResult(null);
    try {
      // The same filter values are passed to the real discovery
      // request too -- the backend's ArbeitnowProvider already
      // supports a location text filter (confirmed this session),
      // this just finally exposes it in the UI.
      const result = await api.discoverJobs({
        location: locationFilter.trim() || undefined,
        remote_only: remoteOnly || undefined,
      });
      setDiscoveryResult(result);
      await loadListings();
    } catch (err) {
      setDiscoveryError(err);
    } finally {
      setDiscovering(false);
    }
  }

  return (
    <div>
      <h1>Job Discovery</h1>

      {/* Section 8: the configured preference is shown as exactly
          that -- a preference -- never as active provider-side
          filtering, which does not exist for the current provider. */}
      <p style={{ color: "#555", fontSize: "0.9rem" }}>
        Your configured salary preference: £40,000 &ndash; £110,000. The current job provider does not disclose
        salary data, so this preference cannot currently be used to filter results -- see each listing below.
      </p>

      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap", marginBottom: "1rem" }}>
        <label>
          Location filter{" "}
          <input
            type="text"
            placeholder="e.g. Birmingham, London, UK"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            style={{ padding: "0.4rem" }}
          />
        </label>
        <label>
          <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} /> Remote only
        </label>
      </div>
      <p style={{ color: "#999", fontSize: "0.8rem", marginTop: "-0.5rem" }}>
        This matches the exact text of each listing's location as reported by the provider -- it is not a
        real distance/postcode radius search.
      </p>

      <button onClick={handleDiscover} disabled={discovering} style={{ padding: "0.6rem 1rem", cursor: "pointer", marginBottom: "1rem" }}>
        {discovering ? "Discovering..." : "Discover Jobs"}
      </button>

      {discoveryError !== null && <ErrorState error={discoveryError} />}
      {discoveryResult && (
        <div style={{ padding: "0.5rem", background: "#f0f7f0", borderRadius: 4, marginBottom: "1rem" }}>
          <div>
            Found {discoveryResult.listings_found} listing(s) from {discoveryResult.provider_name}:{" "}
            {discoveryResult.listings_new} new, {discoveryResult.listings_duplicate} already known.
          </div>
          {/* Surfacing the actual search term used -- previously
              captured in state but never shown, which made it
              impossible to tell whether a search was genuinely
              derived from Career DNA or empty/generic. */}
          <div style={{ fontSize: "0.85rem", color: "#555", marginTop: "0.25rem" }}>
            Search term used: {discoveryResult.query_used ? `"${discoveryResult.query_used}"` : "(none -- returned the provider's unfiltered results)"}
          </div>
        </div>
      )}

      {error !== null && <ErrorState error={error} />}
      {listings === null && error === null && <LoadingState label="Loading job listings..." />}
      {listings !== null && listings.length === 0 && (
        <EmptyState message="No job listings yet. Click 'Discover Jobs' to search." />
      )}

      {filteredListings !== null && listings !== null && listings.length > 0 && (
        <>
          <p style={{ color: "#555" }}>
            {filteredListings.length} of {total} total listing(s)
            {(locationFilter || remoteOnly) && filteredListings.length === 0 && (
              <> &mdash; no listings currently match this filter. Try "Discover Jobs" again with a broader location, or clear the filter.</>
            )}
          </p>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {filteredListings.map((listing) => (
              <li key={listing.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: "1rem", marginBottom: "0.75rem" }}>
                <strong>{listing.title}</strong>
                <div style={{ color: "#555" }}>{listing.company_name_raw}</div>
                <div style={{ fontSize: "0.9rem", color: "#777" }}>
                  {listing.location_raw ?? "Location not specified"}
                  {listing.is_remote && " (Remote)"}
                </div>
                <div style={{ fontSize: "0.9rem", marginTop: "0.25rem" }}>
                  <SalaryDisplay listing={listing} />
                </div>
                {listing.posted_at && (
                  <div style={{ fontSize: "0.8rem", color: "#999" }}>
                    Posted: {new Date(listing.posted_at).toLocaleDateString()}
                  </div>
                )}
                <a href={listing.source_url} target="_blank" rel="noopener noreferrer" style={{ display: "inline-block", marginTop: "0.5rem" }}>
                  View original listing &rarr;
                </a>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
