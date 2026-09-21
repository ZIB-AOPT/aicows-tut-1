import gurobipy as gp
from gurobipy import GRB


def main() -> None:
    model = gp.Model("full-license-check")
    model.Params.OutputFlag = 0

    x = model.addVars(2101, vtype=GRB.BINARY)
    model.addConstr(gp.quicksum(x.values()) <= 1)
    model.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)
    model.optimize()

    assert model.Status == GRB.OPTIMAL
    print("Full Gurobi license check OK")


if __name__ == "__main__":
    main()
