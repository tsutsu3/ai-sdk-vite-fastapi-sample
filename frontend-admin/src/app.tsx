import { Resource } from "ra-core";
import { Admin } from "@/components/admin";
import { ListGuesser } from "@/components/list-guesser";
import { dataProvider } from "./data-provider";

const App = () => (
  <Admin dataProvider={dataProvider}>
    <Resource name="users" list={ListGuesser} />
  </Admin>
);

export default App;
