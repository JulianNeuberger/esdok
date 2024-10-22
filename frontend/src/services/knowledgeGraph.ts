interface Aspect {
    name: string;
    shape: "rect" | "parallelogram" | "rounded" | undefined;
    color: string;
}

export interface Node {
    id: string;
    name: string;
    type: string;
    aspect: Aspect;
    position: {x: number, y: number};
}

export interface Edge {
    id: string;
    type: string;
    source: Node;
    target: Node;
}

export interface KnowledgeGraph {
    nodes: Node[];
    edges: Edge[];
}

export class KnowledgeGraphService {

    public listGraphs = async (): Promise<string[]> => {
        const response = await fetch(` http://127.0.0.1:5000/graph/`);
        return response.json();
    }

    public load = async (metaModel: string): Promise<KnowledgeGraph | undefined> => {
        const response = await fetch(` http://127.0.0.1:5000/graph/${metaModel}/`, {
            method: "GET"
        });
        const json = await response.json();
        if(!Object.hasOwn(json, "nodes")) {
            return undefined;
        }
        if(!Object.hasOwn(json, "edges")) {
            return undefined;
        }
        return json;
    }

    public extract = async (file: File, metaModel: string): Promise<boolean> => {
        const data = new FormData();
        data.append("file", file);
        data.append("metaModel", metaModel);

        const response = await fetch(" http://127.0.0.1:5000/graph/extract/", {
            method: "POST",
            body: data
        });

        const json = await response.json();
        return json["success"];
    }

    public layout = async (metaModel: string) => {
        const response = await fetch(` http://127.0.0.1:5000/graph/${metaModel}/layout/`, {
            method: "GET",
        });
        const json = await response.json();
        return json["success"];
    }

    public delete = async (metaModel: string) => {
        await fetch(`http://127.0.0.1:5000/graph/${metaModel}/`, {
            method: "DELETE"
        });
    }
}