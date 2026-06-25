export default function handler(req, res) {
  res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate");
  res.json({
    API_BASE_URL: process.env.API_BASE_URL || "",
    APP_PASSWORD: process.env.APP_PASSWORD || "",
  });
}
