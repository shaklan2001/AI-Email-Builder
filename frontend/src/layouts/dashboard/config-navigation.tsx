import SvgColor from "src/components/svg-color";

const icon = (name: string) => (
  <SvgColor src={`/assets/icons/navbar/${name}.svg`} sx={{ width: 1, height: 1 }} />
);

const ICONS = {
  dashboard: icon("ic_dashboard"),
  mail: icon("ic_mail"),
};

export const navData = [
  {
    subheader: "Overview",
    items: [
      {
        title: "Dashboard",
        path: "/dashboard",
        icon: ICONS.dashboard,
      },
    ],
  },
  {
    subheader: "Campaigns",
    items: [
      {
        title: "New Campaign",
        path: "/campaigns/new",
        icon: ICONS.mail,
      },
    ],
  },
];
