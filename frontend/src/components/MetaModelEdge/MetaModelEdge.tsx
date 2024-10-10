import React, {type FC} from 'react';
import {BaseEdge, type Edge, EdgeLabelRenderer, type EdgeProps, getBezierPath,} from '@xyflow/react';
import {MetaModelService, Relation} from "../../services/metaModelService";
import {CloseOutlined, DownOutlined, SaveOutlined} from "@ant-design/icons";
import {Button, Form, Input} from "antd";
import TextArea from "antd/es/input/TextArea";

const MetaModelEdge: FC<EdgeProps<Edge<{ relation: Relation, persisted: boolean }>>> = ({
   id,
   sourceX,
   sourceY,
   targetX,
   targetY,
   sourcePosition,
   targetPosition,
   data,
}) => {
    const [isOpen, setIsOpen] = React.useState(false);

    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    const [isLoading, setIsLoading] = React.useState(false);
    const [relation, setRelation] = React.useState<Relation | undefined>(data?.relation);

    const metaModelService = new MetaModelService();

    const renderName = () => {
        if(!relation) return undefined;
        if(data?.persisted) {
            return <>{relation.name}</>;
        }
        return (
            <Input
                value={relation.name}
                onChange={e => setRelation({...relation, name: e.target.value})}
            />
        );
    }

    const renderForm = () => {
        if(!relation) {
            return <>?</>;
        }
        if(!isOpen) {
            if(data?.persisted) {
                return <span>{relation.name}</span>;
            }
            return <span style={{fontStyle: "italic"}}>New Relation</span>
        }
        return (
            <Form
                style={{pointerEvents: "all"}}
            >
                <Form.Item>{renderName()}</Form.Item>
                <Form.Item>
                    <TextArea value={relation.description} onChange={(e) => setRelation({
                        ...relation,
                        description: e.target.value
                    })}/>
                </Form.Item>
                <Form.Item>
                    <Button
                        type={"primary"}
                        onClick={async () => {
                            console.log(relation);
                            if(!relation) return;
                            setIsLoading(true);
                            await metaModelService.patchModel([], [relation])
                            setIsLoading(false);
                        }}
                        disabled={!relation || isLoading}
                        loading={isLoading}
                        icon={<SaveOutlined />}
                    >
                        Save
                    </Button>
                </Form.Item>
            </Form>
        );
    }

    return (
        <>
            <BaseEdge id={id} path={edgePath} />
            <EdgeLabelRenderer>
                <div
                    style={{
                        position: 'absolute',
                        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                        padding: 10,
                        paddingRight: 30,
                        borderRadius: 5,
                        border: "solid 1px black",
                        backgroundColor: "white",
                        fontSize: 12,
                        fontWeight: 700,
                    }}
                    className="nodrag nopan"
                >
                    <Button
                        type={"text"}
                        shape={"circle"}
                        size={"small"}
                        icon={isOpen ? <CloseOutlined /> : <DownOutlined /> }
                        style={{
                            pointerEvents: "all",
                            position: "absolute",
                            right: 5,
                            top: 7,
                        }}
                        onClick={() => setIsOpen(!isOpen)}
                    />
                    {renderForm()}
                </div>
            </EdgeLabelRenderer>
        </>
    );
}

export default MetaModelEdge;