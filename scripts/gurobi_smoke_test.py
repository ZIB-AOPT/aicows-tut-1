import gurobipy as gp
from gurobipy import GRB


def main() -> None:
    model = gp.Model("workshop-smoke-test")

    x = model.addVar(vtype=GRB.BINARY, name="x")
    y = model.addVar(vtype=GRB.BINARY, name="y")

    model.addConstr(x + y <= 1)
    model.setObjective(2 * x + y, GRB.MAXIMIZE)
    model.optimize()

    assert model.Status == GRB.OPTIMAL
    assert round(model.ObjVal) == 2

    print("Gurobi smoke test OK")
    print(f"x={x.X:g}, y={y.X:g}, objective={model.ObjVal:g}")


if __name__ == "__main__":
    main()
